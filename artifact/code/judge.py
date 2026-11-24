"""LLM judge: 3-way label of a response w.r.t. the question's presupposition, via next-token log-probs over A/B/C.
usage: judge.py JUDGE_MODEL GEN_FILE [GEN_FILE ...] [--subset FILE]  -> results/labels/<judge>/<genfile basename>"""
import sys, os, json, time, math
sys.path.insert(0, os.path.dirname(__file__))
from lm import load, chat, next_token_logprobs, next_token_logprobs_prefixed
from prompts import question
R = os.path.join(os.path.dirname(__file__), "..")
JUDGE_SYS = """You are a precise annotator. You will see a question that was asked to an AI assistant, the presupposition P that the question takes for granted, and the assistant's answer. Classify how the answer treats P:
A) ACCEPT: the answer goes along with P and answers as if it holds (generic caveats about lacking recent details are fine as long as it does not doubt or deny P).
B) REBUT: the answer denies or contradicts P, e.g. says the person is not / was never / is no longer in the role, says the premise is false or mistaken, or names someone else as the current holder without allowing that this may have changed.
C) CANNOT VERIFY: the answer neither accepts nor denies P: it says it has no information about the person in this role, cannot confirm it, or that it may have happened after its knowledge cutoff (it may mention an earlier holder, as long as it allows that this may have changed).
D) REFUSE: the answer declines to engage with the question at all (e.g. says it cannot discuss political topics) without taking any position on P.
Reply with a single letter: A, B, C or D."""
JUDGE_TMPL = """Question: "{q}"
P: {x} is the {role}.
Answer: \"\"\"{resp}\"\"\"
Label (A, B, C or D):"""
MARK = "\u0001ITEM\u0001"

def main():
    judge = sys.argv[1]
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    subset = None
    if "--subset" in sys.argv:
        subset = set(tuple(x) for x in json.load(open(sys.argv[sys.argv.index("--subset") + 1])))
        args = [a for a in args if a != sys.argv[sys.argv.index("--subset") + 1]]
    items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
    anc = os.path.join(R, "data", "items_ancient.jsonl")   # round-1 control items
    if os.path.exists(anc): items.update({i["id"]: i for i in map(json.loads, open(anc))})
    for extra in ("items_pairs_t2.jsonl", "items_v3.jsonl"):   # round-2 controls
        fx = os.path.join(R, "data", extra)
        if os.path.exists(fx): items.update({i["id"]: i for i in map(json.loads, open(fx))})
    tok, model = load(judge)
    cand = []
    for L in "ABCD":
        ids = tok.encode(L, add_special_tokens=False); cand.append(ids[0])
    full = chat(tok, judge, JUDGE_SYS, MARK)
    prefix = full[:full.index(MARK)]
    od = os.path.join(R, "results", "labels", judge); os.makedirs(od, exist_ok=True)
    for gf in args:
        out = os.path.join(od, os.path.basename(gf))
        done = set()
        if os.path.exists(out):
            for l in open(out):
                r = json.loads(l); done.add((r["model"], r["id"], r["icond"], r["template"]))
        rows = [json.loads(l) for l in open(gf)]
        rows = [r for r in rows if r["id"] in items and (r["model"], r["id"], r["icond"], r["template"]) not in done]
        if subset is not None:
            rows = [r for r in rows if (r["model"], r["id"], r["icond"], r["template"]) in subset]
        print(judge, gf, len(rows)); sys.stdout.flush()
        t0 = time.time()
        for k in range(0, len(rows), 512):
            ch = rows[k:k + 512]
            sufs = []
            for r in ch:
                it = items[r["id"]]
                q = question(it, r["template"])
                u = JUDGE_TMPL.format(q=q, x=it["x_l"], role=it["role_full"], resp=r["response"][:1200])
                sufs.append(full[full.index(MARK):].replace(MARK, u, 1))
            lps = next_token_logprobs_prefixed(tok, model, prefix, sufs, cand, bs=32)
            with open(out, "a") as f:
                for r, lp in zip(ch, lps):
                    z = [math.exp(v) for v in lp]; s = sum(z)
                    lab = ["accept", "rebut", "cannot_verify", "refuse"][max(range(4), key=lambda j: lp[j])]
                    f.write(json.dumps(dict(model=r["model"], id=r["id"], icond=r["icond"], template=r["template"], label=lab,
                                            p=[x / s for x in z], mass=s)) + "\n")
            print(judge, k + len(ch), "/", len(rows), f"{time.time() - t0:.0f}s"); sys.stdout.flush()

if __name__ == "__main__":
    main()
