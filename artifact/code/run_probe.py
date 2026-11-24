"""Date-probing for effective knowledge cutoff: for each transition (old holder A -> new holder B at date t),
compare log P(B) vs log P(A) as the answer to 'Who is the current <role>?'. Writes results/probe/<model>.jsonl"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from lm import load, chat, continuation_logprob
R = os.path.join(os.path.dirname(__file__), "..")
name = sys.argv[1]
P = [json.loads(l) for l in open(os.path.join(R, "data", "probe.jsonl"))]
os.makedirs(os.path.join(R, "results", "probe"), exist_ok=True)
out = os.path.join(R, "results", "probe", f"{name}.jsonl")
if os.path.exists(out): print("exists", out); sys.exit()
tok, model = load(name)
pref = [chat(tok, name, None, f"Who is the {p['role_full']}? Answer with the person's name only.") for p in P]
t = time.time()
lb = continuation_logprob(tok, model, pref, [p["new_l"] for p in P], bs=32)
la = continuation_logprob(tok, model, pref, [p["old_l"] for p in P], bs=32)
with open(out, "w") as f:
    for p, b, a in zip(P, lb, la):
        f.write(json.dumps(dict(ent=p["ent"], rel=p["rel"], t_change=p["t_change"], quarter=p["quarter"], new_l=p["new_l"], old_l=p["old_l"],
                                lp_new=b[0], n_new=b[1], lp_old=a[0], n_old=a[1])) + "\n")
print(name, "probe done", time.time() - t)
