"""Qualitative examples (logged spot-checks) -> sections/appendix_e_examples_table.tex and results/analysis/spotcheck.jsonl.
Picks, with a fixed seed, responses per (item type, condition, judge label) for a NEW-post item and logs a random
stratified spot-check sample of 60 judged responses with both judges' and the rules' labels."""
import json, os, glob, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from rules import label as rule_label
from prompts import question
from plotstyle import PRETTY
R = os.path.join(os.path.dirname(__file__), "..")
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
gens = {}
for f in glob.glob(os.path.join(R, "results", "gen", "*.jsonl")):
    if "_sweep" in f: continue
    for l in open(f):
        r = json.loads(l); gens[(r["model"], r["id"], r["icond"], r["template"])] = r["response"]
def labels(j):
    L = {}
    for f in glob.glob(os.path.join(R, "results", "labels", j, "*.jsonl")):
        for l in open(f):
            if f.endswith(("_sweep.jsonl", "_anc.jsonl", "_long.jsonl", "_v3.jsonl", "_pairs_t2.jsonl")): break
            r = json.loads(l); L[(r["model"], r["id"], r["icond"], r["template"])] = r["label"]
    return L
LQ, LM, LH = labels("qwen2.5-7b"), labels("mistral-7b"), labels("claude-haiku-5-5")
LQ_ALL = LQ; LQ = LH   # examples are sampled by the primary judge's label (Claude Haiku 5.5); Qwen kept for the spot-check log
rng = random.Random(7)
def tex(s): return s.replace("\\", "").replace("&", r"\&").replace("%", r"\%").replace("$", r"\$").replace("#", r"\#").replace("_", r"\_").replace("{", "").replace("}", "").replace("~", "").replace("^", "").replace("\n", " ")
want = [("NEW", "plain", "rebut"), ("NEW", "premise", "rebut"), ("NEW", "policy", "cannot_verify"), ("NEW", "rag_stale_u", "rebut"),
        ("NEVER", "premise", "rebut"), ("NEVER", "plain", "accept"), ("STALE_POST", "rag_fresh", "rebut"), ("NEW", "date", "rebut")]
rows = []
EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))
keys = sorted(k for k in LQ if k[1] not in EXCL)   # audited items only
for cond, ic, lab in want:
    cand = [k for k in keys if k in gens and k[2] == ic and LQ[k] == lab and items[k[1]]["cond"] == cond and k[0] in ("qwen2.5-7b", "mistral-7b", "phi3.5-mini", "qwen2.5-3b")
            and (cond != "NEW" or items[k[1]]["t_change"] >= "2025-01-01")]
    if not cand: continue
    k = rng.choice(cand); it = items[k[1]]
    rows.append((cond, ic, lab, k, question(it, k[3]), gens[k]))
# 2026-11-20 layout: ragged-right cells (no stretched inter-word spaces), a little air between examples
L = [r"\begin{table*}[t]\centering\small", r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.7cm}>{\raggedright\arraybackslash}p{4.4cm}>{\raggedright\arraybackslash}p{8.0cm}@{}}", r"\toprule", r"Item / condition & Question & Response (first 48 tokens) $\rightarrow$ judge label \\", r"\midrule"]
for cond, ic, lab, k, q, resp in rows:
    extra = f" (true since {items[k[1]]['t_change']})" if cond == "NEW" else ""
    L.append(f"{cond.replace('_', '-')}{extra}; {ic.replace('_', '-')}; {PRETTY[k[0]]} & {tex(q)} & {tex(resp[:330])}\\,\\ldots{{}} $\\rightarrow$ \\textbf{{{lab.replace('_', ' ')}}} \\\\[2pt]")
L += [r"\bottomrule\end{tabular}", r"\caption{Logged examples, sampled with a fixed seed from responses with the given judge label. Responses are truncated.}", r"\label{tab:examples}\end{table*}"]
open(os.path.join(R, "tables", "examples.tex"), "w").write("\n".join(L) + "\n")
# spot-check log
sub = [k for k in keys if k in LM and k in gens]
rng.shuffle(sub)
with open(os.path.join(R, "results", "analysis", "spotcheck.jsonl"), "w") as f:
    for k in sub[:60]:
        f.write(json.dumps(dict(model=k[0], id=k[1], icond=k[2], question=question(items[k[1]], k[3]), presupposition=f"{items[k[1]]['x_l']} is the {items[k[1]]['role_full']}",
                                truth=items[k[1]]["truth"], response=gens[k], haiku=LH.get(k), qwen=LQ_ALL.get(k), mistral=LM[k], rules=rule_label(gens[k]))) + "\n")
print("examples", len(rows))
