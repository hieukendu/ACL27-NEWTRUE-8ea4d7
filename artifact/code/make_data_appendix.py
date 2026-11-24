"""Writes sections/appendix_a_data.tex (item counts, validation log, examples) from data/."""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
from texalign import pad_cols
R = os.path.join(os.path.dirname(__file__), "..")
I_all = [json.loads(l) for l in open(os.path.join(R, "data", "items.jsonl"))]
EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))
# round 3: the withdrawn T1/T3 ANC control is no longer listed; the triples (FORMER, SWAP) come from items_v3.jsonl
V3 = [json.loads(l) for l in open(os.path.join(R, "data", "items_v3.jsonl"))]
V3 = [i for i in V3 if i["pair"] not in EXCL]
I = [i for i in I_all if i["id"] not in EXCL] + [i for i in V3 if i["cond"] in ("P3_ANC", "P3_SWAP")]
V = json.load(open(os.path.join(R, "data", "validation_log.json")))
REL = {"P6": "Head of gov. (P6)", "P35": "Head of state (P35)", "P169": "CEO (P169)", "P286": "Head coach (P286)", "P488": "Chairperson (P488)"}
def grp(i):
    if i["cond"] == "NEW": return "NEW-post" if i["t_change"] >= "2025-01-01" else "NEW-near"
    if i["cond"] == "STALE_PRE": return "STALE<2021" if i["t_change"] < "2021-01-01" else "STALE21-22"
    if i["cond"] == "P3_ANC": return "FORMER"
    if i["cond"] == "P3_SWAP": return "SWAP"
    return i["cond"].replace("_", "-")
RS = {"P6": ("Gov.",), "P35": ("State",), "P169": ("CEO",), "P286": ("Coach",), "P488": ("Chair",)}
G = ["NEW-post", "NEW-near", "OLD", "STALE<2021", "STALE21-22", "STALE-POST", "NEVER", "FORMER", "SWAP"]
c = collections.Counter((i["rel"], grp(i)) for i in I)
L = [r"\section{Benchmark Details}", r"\label{app:data}",
     r"Table~\ref{tab:data} counts audited items from the 2026-11-10 Wikidata and English Wikipedia snapshot. Columns are heads of government (P6) and state (P35), CEOs (P169), head coaches (P286) and chairpersons (P488). NEW-post changes begin in 2025; NEW-near covers July 2023--December 2024. The STALE rows distinguish replacements before 2021, in 2021--mid-2022, and predecessors of NEW-post holders. These groups span different histories, so their assigned-template rates should not be read as a single matched comparison.",
     r"FORMER and SWAP supply the two false premises in each of the 35 entity triples. Their NEW premises reuse the corresponding NEW-post items and are not counted again. FORMER is a living holder whose last term ended before 2016; SWAP is another entity's holder appointed since 2025. The main grid uses assigned templates T1--T3, while the triples use present-tense T2.",
     # 2026-11-20 layout: transposed (conditions as rows, relations as columns) to fit one column without \resizebox
     r"\begin{table}[t]\centering\small\setlength\tabcolsep{4.5pt}", r"\begin{tabular}{@{}l" + "c" * (len(REL) + 1) + "@{}}", r"\toprule",
     "Condition & " + " & ".join(RS[r][0] for r in REL) + r" & All \\",
     " & " + " & ".join(r"{\footnotesize %s}" % r for r in REL) + r" & \\", r"\midrule"]
for k, g in enumerate(G):
    if g == "FORMER": L.append(r"\midrule")
    row = [c[(rel, g)] for rel in REL]; L.append(g.replace("<", "$<$") + " & " + " & ".join(map(str, row)) + f" & {sum(row)} \\\\")
tot = [sum(c[(rel, g)] for g in G) for rel in REL]
L += [r"\midrule", "All & " + " & ".join(map(str, tot)) + f" & {sum(tot)} \\\\", r"\bottomrule\end{tabular}",
      r"\caption{Audited items by premise type and relation. The last two premise rows add false controls for %d triples; their true NEW members are already counted in NEW-post.}\label{tab:data}\end{table}" % len({i["pair"] for i in V3})]
pad_cols(L, range(1, len(REL) + 2))
L.append(f"\\paragraph{{Audit.}} After review, {len(EXCL)} items were removed (\\texttt{{data/exclusions.json}}, with the deciding Wikipedia sentence in \\texttt{{results/audit/verdicts.json}}): "
         + ", ".join(f"{i['x_l']} ({i['cond']})" for i in I_all if i["id"] in EXCL) + ". "
         "Claude Haiku 5.5 flagged items whose gold truth contradicted its own knowledge; each flagged item was kept or removed after checking the person's current English Wikipedia article. "
         "NEW items whose holder had held the same role before (reinstatements) were removed using earlier Wikidata terms and the Wikipedia leads of flagged items. "
         "Every NEW holder's Wikipedia lead was also checked by rule for disambiguation pages, acting or interim holders and a missing entity name (\\texttt{code/audit\\_new.py}); a past-tense check of the lead was not implemented. "
         "OLD-0315 (Andrey Kondrashov, TASS) was removed in round three after a reviewer noted, and the TASS article confirmed, that he took office in July 2023. "
         "The excluded acting holder Albulena Haxhiu still appears as the SWAP person of one triple; the premise is false either way.")
kept = sum(v for k, v in V.items() if k.startswith("keep_")); drop = sum(v for k, v in V.items() if k.startswith("drop_"))
L.append(f"Of {kept + drop} candidate items, {drop} ({100 * drop / (kept + drop):.0f}\\%) failed the Wikipedia corroboration check and were dropped "
         f"(per condition: " + ", ".join(f"{k[5:].replace('_', '-')} {v}" for k, v in V.items() if k.startswith('drop_')) +
         f"). {V.get('office_label_replaced', 0)} office labels failed the P39 consistency check and were replaced by the generic role phrase.")
L.append(r"\paragraph{Validation.}")
sl = sorted(i["y_sl"] for i in I)
L.append(f"Entity popularity (Wikidata sitelinks) ranges from {sl[0]} to {sl[-1]} (median {sl[len(sl)//2]}).")
L.append(r"\paragraph{Examples.}\begin{itemize}\small")
tr = [i for i in V3 if i["pair"] == "NEW-0006"]   # one complete triple (Disney)
for i in sorted(tr, key=lambda i: ["P3_NEW", "P3_ANC", "P3_SWAP"].index(i["cond"])):
    nm = {"P3_NEW": "Triple, NEW", "P3_ANC": "Triple, FORMER", "P3_SWAP": "Triple, SWAP"}[i["cond"]]
    L.append(f"\\item {nm}: \\textit{{{i['x_l']}}} as \\textit{{{i['role_full']}}}" + (f" (change: {i['t_change']})" if i["cond"] == "P3_NEW" else "") + ".")
seen = set()
for i in I:
    g = grp(i)
    if g in seen or g in ("NEW-near", "NEW-post"): continue
    if g in ("FORMER", "SWAP"): continue
    seen.add(g)
    x = i["x_l"].replace("&", r"\&"); rf = i["role_full"].replace("&", r"\&")
    extra = f" (change: {i['t_change']})" if i.get("t_change") and g != "OLD" else ""
    L.append(f"\\item {g}: \\textit{{{x}}} as \\textit{{{rf}}}{extra}.")
L.append(r"\end{itemize}")
open(os.path.join(R, "sections", "appendix_a_data.tex"), "w").write("\n".join(L) + "\n")
print("ok", sum(tot))
