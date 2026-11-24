"""Shared model loading / batched greedy generation / scoring (Apple MPS locally; CUDA on the GX10 server)."""
import torch, time
from transformers import AutoTokenizer, AutoModelForCausalLM

MODELS = {
    "qwen2.5-0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "qwen2.5-1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
    "qwen2.5-3b":   "Qwen/Qwen2.5-3B-Instruct",
    "qwen2.5-7b":   "Qwen/Qwen2.5-7B-Instruct",
    "mistral-7b":   "mistralai/Mistral-7B-Instruct-v0.3",
    "phi3.5-mini":  "microsoft/Phi-3.5-mini-instruct",
    "smollm2-1.7b": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    "qwen3.5-4b":   "Qwen/Qwen3.5-4B",
    # round-2 scale-up (run on the GX10 server, NVIDIA GB10): larger, ungated open models
    "qwen2.5-14b":  "Qwen/Qwen2.5-14B-Instruct",
    "qwen2.5-32b":  "Qwen/Qwen2.5-32B-Instruct",
    "phi4":         "microsoft/phi-4",
    "mistral-small-24b": "mistralai/Mistral-Small-24B-Instruct-2501",
}
DEV = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")

def load(name):
    mid = MODELS[name]
    tok = AutoTokenizer.from_pretrained(mid)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(mid, dtype=torch.bfloat16).to(DEV).eval()
    return tok, model

def chat(tok, name, system, user, prefill=""):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    kw = {"enable_thinking": False} if name.startswith("qwen3") else {}
    s = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **kw)
    return s + prefill

@torch.no_grad()
def generate(tok, model, prompts, max_new_tokens=64, bs=16):
    order = sorted(range(len(prompts)), key=lambda i: -len(prompts[i]))
    out = [None] * len(prompts)
    for b in range(0, len(order), bs):
        idx = order[b:b + bs]
        enc = tok([prompts[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False).to(DEV)
        g = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, temperature=None, top_p=None, top_k=None,
                           pad_token_id=tok.pad_token_id)
        for j, i in enumerate(idx):
            out[i] = tok.decode(g[j, enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return out

@torch.no_grad()
def next_token_logprobs(tok, model, prompts, cand_ids, bs=16):
    """Return log-probs (over full vocab) of candidate token ids at next position."""
    res = [None] * len(prompts)
    order = sorted(range(len(prompts)), key=lambda i: -len(prompts[i]))
    for b in range(0, len(order), bs):
        idx = order[b:b + bs]
        enc = tok([prompts[i] for i in idx], return_tensors="pt", padding=True, add_special_tokens=False).to(DEV)
        logits = model(**enc, logits_to_keep=1).logits[:, -1, :].float()
        lp = torch.log_softmax(logits, -1)[:, cand_ids].cpu().tolist()
        for j, i in enumerate(idx):
            res[i] = lp[j]
    return res

@torch.no_grad()
def continuation_logprob(tok, model, prefixes, conts, bs=16):
    """Sum log-prob of cont given prefix (prefix already chat-formatted). Returns (sum, ntokens)."""
    res = [None] * len(prefixes)
    pairs = []
    for p, c in zip(prefixes, conts):
        pi = tok(p, add_special_tokens=False)["input_ids"]
        ci = tok(c, add_special_tokens=False)["input_ids"]
        pairs.append((pi, ci))
    order = sorted(range(len(pairs)), key=lambda i: -(len(pairs[i][0]) + len(pairs[i][1])))
    pad = tok.pad_token_id
    for b in range(0, len(order), bs):
        idx = order[b:b + bs]
        seqs = [pairs[i][0] + pairs[i][1] for i in idx]
        L = max(len(s) for s in seqs)
        ids = torch.full((len(seqs), L), pad); att = torch.zeros((len(seqs), L), dtype=torch.long)
        for j, s in enumerate(seqs):
            ids[j, L - len(s):] = torch.tensor(s); att[j, L - len(s):] = 1
        ids, att = ids.to(DEV), att.to(DEV)
        logits = model(input_ids=ids, attention_mask=att).logits.float()
        lp = torch.log_softmax(logits[:, :-1], -1)
        tgt = ids[:, 1:]
        tl = lp.gather(-1, tgt.unsqueeze(-1)).squeeze(-1).cpu()
        for j, i in enumerate(idx):
            n = len(pairs[i][1]); s = tl[j, -n:].sum().item()
            res[i] = (s, n)
    return res

@torch.no_grad()
def next_token_logprobs_prefixed(tok, model, prefix, suffixes, cand_ids, bs=32):
    """Same as next_token_logprobs for prompts prefix+suffix_i, but the shared prefix is encoded once and its KV cache
    is reused (right padding; logits taken at each row's last real token)."""
    import copy
    pre = tok(prefix, return_tensors="pt", add_special_tokens=False)["input_ids"].to(DEV)
    base = model(input_ids=pre, use_cache=True).past_key_values
    P = pre.shape[1]
    res = [None] * len(suffixes)
    enc_all = [tok(s, add_special_tokens=False)["input_ids"] for s in suffixes]
    order = sorted(range(len(suffixes)), key=lambda i: -len(enc_all[i]))
    pad = tok.pad_token_id
    for b in range(0, len(order), bs):
        idx = order[b:b + bs]
        L = max(len(enc_all[i]) for i in idx)
        ids = torch.full((len(idx), L), pad); att = torch.zeros((len(idx), P + L), dtype=torch.long); att[:, :P] = 1
        last = []
        for j, i in enumerate(idx):
            s = enc_all[i]; ids[j, :len(s)] = torch.tensor(s); att[j, P:P + len(s)] = 1; last.append(len(s) - 1)
        cache = copy.deepcopy(base); cache.batch_repeat_interleave(len(idx))
        out = model.model(input_ids=ids.to(DEV), attention_mask=att.to(DEV), past_key_values=cache, use_cache=True)
        h = out.last_hidden_state[torch.arange(len(idx)), torch.tensor(last)]
        lp = torch.log_softmax(model.lm_head(h).float(), -1)[:, cand_ids].cpu().tolist()
        for j, i in enumerate(idx):
            res[i] = lp[j]
    return res
