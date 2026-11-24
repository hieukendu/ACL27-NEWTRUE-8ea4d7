"""Yes/No premise verifier: P(No) for 'Is it true that X is the ROLE?' (plain and with today's date).
Thresholding P(No) gives a continuous premise-checking policy (rebut iff P(No) > tau). results/verify/<model>.jsonl"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from lm import load, chat, next_token_logprobs
from prompts import TODAY
R = os.path.join(os.path.dirname(__file__), "..")
name = sys.argv[1]
I = [json.loads(l) for l in open(os.path.join(R, "data", "items.jsonl"))]
os.makedirs(os.path.join(R, "results", "verify"), exist_ok=True)
out = os.path.join(R, "results", "verify", f"{name}.jsonl")
if os.path.exists(out): sys.exit()
tok, model = load(name)
yes = [tok.encode(w, add_special_tokens=False)[0] for w in ("Yes", " Yes")]
no = [tok.encode(w, add_special_tokens=False)[0] for w in ("No", " No")]
rows = []
for var, sysmsg in (("plain", None), ("date", f"Today's date is {TODAY}.")):
    ps = [chat(tok, name, sysmsg, f"Is it true that {i['x_l']} is the {i['role_full']}? Answer with Yes or No only.") for i in I]
    lps = next_token_logprobs(tok, model, ps, yes + no, bs=32)
    for i, lp in zip(I, lps):
        py = sum(math.exp(v) for v in lp[:2]); pn = sum(math.exp(v) for v in lp[2:])
        rows.append(dict(id=i["id"], var=var, p_no=pn / (py + pn), mass=py + pn))
with open(out, "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
print(name, "verify done")
