"""Revised tables and macros (round 1) from results/analysis/v2.json -> tables/v2_*.tex and numbers_v2.tex.
Macro naming: \\V<Metric><Cond><Set>[CI], e.g. \\VRebNewPlainAll = rebut rate of NEW-post premises under Plain, all models,
primary judge. Missing cells render as a red \\pending{} so nothing is ever estimated by hand."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from texalign import pad_cols
from plotstyle import MODEL_ORDER, PRETTY
R = os.path.join(os.path.dirname(__file__), "..")
TD = os.path.join(R, "tables"); os.makedirs(TD, exist_ok=True)
V = json.load(open(os.path.join(R, "results", "analysis", "v2.json")))
P, D, PA, PM = V["rates"], V["diffs"], V["paired_anc"], V["per_model"]
J0 = V["primary_judge"]
CONDS = [("plain", "Plain", "Plain"), ("premise", "Premise-check", "Prem"), ("date", "Date", "Date"), ("cutoff_date", "Cutoff-stated", "Cut"),
         ("rag_fresh", "RAG-fresh (oracle)", "Ragf"), ("rag_mixed", "RAG-mixed", "Ragm"), ("rag_stale_u", "RAG-stale", "Rags"),
         ("policy", "Policy (ours)", "Pol"), ("policy_nodate", "\\quad -- no date", "Polnd")]
PEND = "\\pending{run}"
def pc(d): return f"{100 * d['mean']:.0f}" if d and d.get("mean") is not None else PEND
def pci(d):
    if not d or d.get("mean") is None: return PEND
    if not d.get("ci") or d["ci"][0] is None: return pc(d)
    return f"{100 * d['mean']:.0f} {{\\scriptsize[{100 * d['ci'][0]:.0f},{100 * d['ci'][1]:.0f}]}}"
def sgn(d):
    if not d or d.get("mean") is None: return PEND
    v = 100 * d["mean"]; return ("+" if v >= 0.5 else ("$-$" if v <= -0.5 else "")) + f"{abs(v):.0f}"
def sgnci(d):
    if not d or d.get("mean") is None: return PEND
    s = sgn(d)
    return s + (f" {{\\scriptsize[{100 * d['ci'][0]:.0f},{100 * d['ci'][1]:.0f}]}}" if d.get("ci") and d["ci"][0] is not None else "")
r = lambda j, s, c, g, L="rebut": P.get(f"{j}|{s}|{c}|{g}|{L}")

# ---- Table 1: main, all models, primary judge
def main_table(S, label, title):
    L = [r"\begin{table*}[t]\centering\small\setlength\tabcolsep{3.4pt}", r"\begin{tabular}{l ccc c c c c}", r"\toprule",
         r" & \multicolumn{2}{c}{rebut true} & \multicolumn{2}{c}{rebut false} & defer & \multicolumn{2}{c}{gaps (pts)} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){7-8}",
         r"Condition & \NEW{}-post & \OLD{} & \ANC{} (paired) & \STRE{} & \NEW{}-post & \NEW{}$-$\OLD{} & $J_{\text{anc}}$ \\", r"\midrule"]
    for c, name, _ in CONDS:
        pa = PA.get(f"{J0}|{S}|{c}")
        L.append(f"{name} & {pci(r(J0, S, c, 'NEW_post'))} & {pc(r(J0, S, c, 'OLD'))} & {pc(dict(mean=pa['rebut_anc']) if pa else None)} & "
                 f"{pc(r(J0, S, c, 'STR_early'))} & {pc(r(J0, S, c, 'NEW_post', 'cannot_verify'))} & "
                 f"{sgnci(D.get(f'{J0}|{S}|{c}|new_minus_old'))} & {sgnci(pa)} \\\\")
        if c in ("plain", "cutoff_date", "rag_stale_u"): L.append(r"\midrule")
    n = V["n_items"]
    L += [r"\bottomrule\end{tabular}",
          r"\caption{%s Rebuttal and deferral rates (\%%), primary judge (Claude Haiku 5.5). True premises: \NEW{}-post ($n{=}%d$, became true on or after 2025-01-01, after every model's release) and \OLD{} ($n{=}%d$, unchanged since 2022 or earlier). False premises: \ANC{} ($n{=}%d$), a holder of the \emph{same} role at the \emph{same} entity who left before 2016, paired with its \NEW{}-post item; \STRE{} ($n{=}%d$), a holder replaced before 2021. $J_{\text{anc}}$ = rebut(\ANC{}) $-$ rebut(paired \NEW{}-post): 0 means the model rebuts a newly-true premise as often as a long-false one about the same entity. 95\%% CIs from a two-level bootstrap over models and items.}"
          % (title, n["NEW_post"], n["OLD"], n.get("ANC", 0), n["STR_early"]),
          f"\\label{{{label}}}\\end{{table*}}"]
    return "\n".join(L) + "\n"
open(os.path.join(TD, "v2_main.tex"), "w").write(main_table("all", "tab:main", "All %d models." % len(V["models_all"])))
open(os.path.join(TD, "v2_know.tex"), "w").write(main_table("know", "tab:know", "The %d models whose date probe shows knowledge of office holders." % len(V["models_know"])).replace("table*}[t]", "table*}[p]"))

# ---- Table 2: per model, paired NEW vs ANC (primary judge)
SEL = [("plain", "Plain"), ("premise", "PC"), ("rag_fresh", "RAG-f"), ("rag_stale_u", "RAG-s"), ("policy", "Policy")]
L = [r"\begin{table*}[t]\centering\small\setlength\tabcolsep{3.4pt}", r"\begin{tabular}{l " + " ".join(["ccc"] * len(SEL)) + "}", r"\toprule",
     " & " + " & ".join(f"\\multicolumn{{3}}{{c}}{{{n}}}" for _, n in SEL) + r" \\",
     "".join(f"\\cmidrule(lr){{{2 + 3 * k}-{4 + 3 * k}}}" for k in range(len(SEL))),
     "Model & " + " & ".join(["\\NEW{} & \\ANC{} & \\OLD{}"] * len(SEL)) + r" \\", r"\midrule"]
for m in [x for x in MODEL_ORDER if x in V["models_all"]]:
    cells = []
    for c, _ in SEL:
        pa = PA.get(f"{J0}|all|{c}", {}).get("per_model", {}).get(m)
        if pa:
            star = "$^{*}$" if pa["p"] < 0.05 else ""
            cells += [f"{100 * pa['rebut_new']:.0f}", f"{100 * pa['rebut_anc']:.0f}{star}", pc(PM.get(f"{m}|{c}|OLD"))]
        else:
            cells += [pc(PM.get(f"{m}|{c}|NEW_post")), PEND, pc(PM.get(f"{m}|{c}|OLD"))]
    L.append(f"{PRETTY[m]} & " + " & ".join(cells) + r" \\")
L += [r"\bottomrule\end{tabular}",
      r"\caption{Per-model rebuttal rates (\%%, primary judge) of newly-true premises (\NEW{}, the %d entities with a matched control), the matched long-false premises about the same entities (\ANC{}) and long-true premises (\OLD{}). $^{*}$: \NEW{} and \ANC{} differ by an exact McNemar test on the paired entities ($p<.05$, uncorrected). PC = Premise-check; RAG-f/-s = fresh (oracle) / stale evidence.}" % V["n_items"].get("ANC", 0),
      r"\label{tab:permodel2}\end{table*}"]
open(os.path.join(TD, "v2_permodel.tex"), "w").write("\n".join(L) + "\n")

# ---- Table 3: judge validation against silver labels
SV = V.get("silver", {})
# 2026-11-20 layout: \small, right-aligned numbers, unit in the header instead of every cell
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{4pt}", r"\begin{tabular}{@{}l rrrrc@{}}", r"\toprule",
     r" & & & \multicolumn{3}{c}{rebut} \\ \cmidrule(l){4-6}",
     r"Judge & acc. & $\kappa$ & P & R & rate (\%) \\", r"\midrule"]
for jn, nm in (("haiku", "Haiku 5.5 (primary)"), ("majority", "3-judge majority"), ("qwen", "Qwen2.5-7B"), ("mistral", "Mistral-7B")):
    s = SV.get(jn)
    if s: L.append(f"{nm} & {s['acc']:.2f} & {s['kappa']:.2f} & {s['rebut_precision']:.2f} & {s['rebut_recall']:.2f} & {100 * s['rebut_rate']:.0f} \\\\")
if SV.get("haiku"): L += [r"\midrule", f"Silver (Sonnet 5.5) & \\multicolumn{{4}}{{c}}{{--}} & {100 * SV['haiku']['silver_rebut_rate']:.0f} \\\\"]
L += [r"\bottomrule\end{tabular}", r"\caption{Agreement with automatic Sonnet 5.5 labels (%d responses). P/R: rebuttal precision/recall. These reference labels are not human judgements.}" % SV.get("n", 0),
      r"\label{tab:silver}\end{table}"]
pad_cols(L, [5]); open(os.path.join(TD, "v2_silver.tex"), "w").write("\n".join(L) + "\n")

# ---- Table 4 (appendix): headline under each judge (all models)
ROWS = [("plain", "NEW_post", "Plain: rebut \\NEW{}-post"), ("plain", "OLD", "\\quad rebut \\OLD{}"), ("plain", "STR_early", "\\quad rebut \\STRE{}"),
        ("premise", "NEW_post", "PC: rebut \\NEW{}-post"), ("premise", "OLD", "\\quad rebut \\OLD{}"), ("rag_fresh", "NEW_post", "RAG-fresh: rebut \\NEW{}-post"),
        ("rag_stale_u", "NEW_post", "RAG-stale: rebut \\NEW{}-post"), ("policy", "NEW_post", "Policy: rebut \\NEW{}-post")]
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{3pt}", r"\begin{tabular}{l cccc}", r"\toprule", r"Rate (\%) & Haiku & Maj. & Qwen & Mistral \\", r"\midrule"]
for c, g, lab in ROWS:
    L.append(lab + " & " + " & ".join(pc(r(j, "all", c, g)) for j in ("haiku", "majority", "qwen", "mistral")) + r" \\")
pa = lambda j: PA.get(f"{j}|all|plain")
L.append("Plain: rebut \\ANC{} (paired) & " + " & ".join(pc(dict(mean=pa(j)["rebut_anc"])) if pa(j) else PEND for j in ("haiku", "majority", "qwen", "mistral")) + r" \\")
L += [r"\bottomrule\end{tabular}", r"\caption{Headline rates (all models) under each judge and the 3-judge majority.}", r"\label{tab:judges2}\end{table}"]
open(os.path.join(TD, "v2_judges.tex"), "w").write("\n".join(L) + "\n")

# ---- Table (appendix): cutoff estimates, summed vs per-token name log-probabilities (results/analysis/round1.json)
r1f = os.path.join(R, "results", "analysis", "round1.json")
if os.path.exists(r1f):
    PN = json.load(open(r1f))["probe_normalised"]
    L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{4pt}", r"\begin{tabular}{@{}l cr cr@{}}", r"\toprule",
         r" & \multicolumn{2}{c}{summed log-prob} & \multicolumn{2}{c}{per-token} \\ \cmidrule(lr){2-3}\cmidrule(l){4-5}", r"Model & step & $p$ & step & $p$ \\", r"\midrule"]
    for m in MODEL_ORDER:
        a, b = PN.get(f"{m}|sum"), PN.get(f"{m}|per_token")
        if a and b: L.append(f"{PRETTY[m]} & {a['cutoff']} & {a['perm_p']:.3f} & {b['cutoff']} & {b['perm_p']:.3f} \\\\")
    L += [r"\bottomrule\end{tabular}", r"\caption{Date-probe change points and permutation $p$-values under two name-scoring rules. \emph{Step} is the month when preference for the new holder drops. Normalisation changes the estimated dates.}", r"\label{tab:cutoffnorm}\end{table}"]
    open(os.path.join(TD, "v2_cutoffnorm.tex"), "w").write("\n".join(L) + "\n")

# ---- macros
N = {}
def put(k, v): N[k] = v
for c, _, tag in CONDS:
    for S, st in (("all", "All"), ("know", "Know")):
        for g, gt in (("NEW_post", "New"), ("OLD", "Old"), ("STR_early", "Stre"), ("NEVER", "Nev"), ("NEW_near", "Near")):
            d = r(J0, S, c, g); put(f"VReb{gt}{tag}{st}", pc(d)); put(f"VReb{gt}{tag}{st}CI", f"[{100 * d['ci'][0]:.0f}, {100 * d['ci'][1]:.0f}]" if d and d.get("ci") and d["ci"][0] is not None else PEND)
        put(f"VDef{tag}{st}", pc(r(J0, S, c, "NEW_post", "cannot_verify"))); put(f"VAccNew{tag}{st}", pc(r(J0, S, c, "NEW_post", "accept")))
        pa = PA.get(f"{J0}|{S}|{c}")
        put(f"VRebAnc{tag}{st}", pc(dict(mean=pa["rebut_anc"])) if pa else PEND); put(f"VRebNewP{tag}{st}", pc(dict(mean=pa["rebut_new"])) if pa else PEND)
        put(f"VJanc{tag}{st}", sgn(pa)); put(f"VJanc{tag}{st}CI", f"[{100 * pa['ci'][0]:.0f}, {100 * pa['ci'][1]:.0f}]" if pa else PEND)
        for nm, mn in (("new_minus_old", "VGapOld"), ("Jpre", "VJpre"), ("Jnev", "VJnev")):
            d = D.get(f"{J0}|{S}|{c}|{nm}"); put(f"{mn}{tag}{st}", sgn(d)); put(f"{mn}{tag}{st}CI", f"[{100 * d['ci'][0]:.0f}, {100 * d['ci'][1]:.0f}]" if d else PEND)
        if c != "plain":
            for g, gt in (("NEW_post", "New"), ("OLD", "Old"), ("ANC", "Anc"), ("STR_early", "Stre")):
                d = D.get(f"{J0}|{S}|{c}|delta|{g}"); put(f"VD{gt}{tag}{st}", sgn(d)); put(f"VD{gt}{tag}{st}CI", f"[{100 * d['ci'][0]:.0f}, {100 * d['ci'][1]:.0f}]" if d else PEND)
    for jn, jt in (("majority", "Maj"), ("qwen", "Q"), ("mistral", "M")):
        for g, gt in (("NEW_post", "New"), ("OLD", "Old"), ("STR_early", "Stre")):
            put(f"VJ{jt}Reb{gt}{tag}", pc(r(jn, "all", c, g)))
        pa = PA.get(f"{jn}|all|{c}"); put(f"VJ{jt}Janc{tag}", sgn(pa))
for g, gt in (("NEW_post", "New"), ("OLD", "Old"), ("ANC", "Anc"), ("STR_early", "Stre"), ("NEVER", "Nev"), ("STALE_POST", "Stp"), ("NEW_near", "Near")):
    put(f"VN{gt}", str(V["n_items"].get(g, 0)))
put("VNExcl", str(V["n_excluded"])); put("VNAll", str(len(V["models_all"]))); put("VNKnow", str(len(V["models_know"])))
put("VNItems", str(sum(V["n_items"].get(g, 0) for g in ("NEW_post", "NEW_near", "OLD", "STR_early", "STR_late", "NEVER", "STALE_POST"))))
for jn, jt in (("haiku", "H"), ("majority", "Maj"), ("qwen", "Q"), ("mistral", "M")):
    s = SV.get(jn)
    if s: put(f"VSil{jt}Acc", f"{s['acc']:.2f}"); put(f"VSil{jt}Kappa", f"{s['kappa']:.2f}"); put(f"VSil{jt}RecRebut", f"{s['rebut_recall']:.2f}"); put(f"VSil{jt}PrecRebut", f"{s['rebut_precision']:.2f}")
put("VSilN", str(SV.get("n", 0)))
def fp(p):
    """p-value for LaTeX math: <0.001 as a power of ten, else two decimals."""
    if p < 0.001:
        import math as _m
        e = int(_m.floor(_m.log10(p))); return f"{p / 10 ** e:.0f}\\times10^{{{e}}}"
    return f"{p:.3f}" if p < 0.01 else f"{p:.2f}"
RG = V.get("regressions", {})
for S, st in (("all", "All"), ("know", "Know")):
    a = RG.get(f"{S}|cond+pop", {})
    if "g[T.OLD]" in a:
        put(f"VRegOld{st}", f"{a['g[T.OLD]']['coef']:.2f}"); put(f"VRegOldP{st}", fp(a['g[T.OLD]']['p']))
        put(f"VRegStre{st}", f"{a['g[T.STR_early]']['coef']:.2f}"); put(f"VRegStreP{st}", fp(a['g[T.STR_early]']['p']))
        if "g[T.ANC]" in a: put(f"VRegAnc{st}", f"{a['g[T.ANC]']['coef']:.2f}"); put(f"VRegAncP{st}", fp(a['g[T.ANC]']['p']))
        put(f"VRegPop{st}", f"{a['logsl']['coef']:.2f}"); put(f"VRegPopP{st}", fp(a['logsl']['p']))
    b = RG.get(f"{S}|person_fame_NEW", {})
    if b:
        put(f"VRegPx{st}", f"{b['logpx']['coef']:.2f}"); put(f"VRegPxP{st}", fp(b['logpx']['p'])); put(f"VRegPxEnt{st}", f"{b['logsl']['coef']:.2f}")
        if "ci" in b["logpx"]: put(f"VRegPxCI{st}", "[{:.2f}, {:.2f}]".format(*b["logpx"]["ci"]).replace("-", "$-$"))
    c_ = RG.get(f"{S}|pop_NEW", {})   # round-3: entity popularity among NEW_post items only
    if c_:
        put(f"VRegPopNew{st}", f"{c_['logsl']['coef']:.2f}"); put(f"VRegPopNewP{st}", fp(c_['logsl']['p']))
        put(f"VRegPopNewCI{st}", "[{:.2f}, {:.2f}]".format(*c_["logsl"]["ci"]).replace("-", "$-$")); put(f"VRegPopNewN{st}", str(c_["n"]))
    if "n" in a: put(f"VRegN{st}", f"{a['n']:,}".replace(",", "{,}"))
LG = V.get("long_generation", {})
for jn, jt in (("haiku", "H"), ("qwen", "Q")):
    for g, gt in (("NEW_post", "New"), ("STR_early", "Stre"), ("OLD", "Old")):
        d = LG.get(f"{jn}|{g}")
        if d: put(f"VLong{jt}{gt}Short", f"{100 * d['rebut_48']:.0f}"); put(f"VLong{jt}{gt}Long", f"{100 * d['rebut_256']:.0f}"); put(f"VLong{jt}{gt}Same", f"{100 * d['same']:.0f}")
# per-model significance counts for the paired test under Plain
pm = PA.get(f"{J0}|all|plain", {}).get("per_model", {})
put("VNSigPairPlain", str(sum(1 for v in pm.values() if v["p"] < .05))); put("VNPairModels", str(len(pm)))
put("VNAncHigherPlain", str(sum(1 for v in pm.values() if v["rebut_anc"] > v["rebut_new"])))
put("VBeliefNewGtStre", str(V.get("belief_new_gt_stre", 0))); put("VBeliefN", str(len(V.get("belief", {}))))
BP = V.get("belief_pooled", {})
if BP: put("VBeliefPoolN", str(BP["n"])); put("VBeliefPoolNewGt", str(BP["new_gt_stre"])); put("VBeliefPoolOldGt", str(BP["old_gt_stre"]))
for c, _, tag in CONDS:
    for S, st in (("all", "All"), ("know", "Know")):
        put(f"VAccFalse{tag}{st}", pc(dict(mean=V["accept_false"][f"{J0}|{S}|{c}"])) if f"{J0}|{S}|{c}" in V.get("accept_false", {}) else PEND)
sf = os.path.join(R, "results", "labels", "silver-claude-sonnet-5-5", "usage.log")
put("VSonnetCost", f"{sum(json.loads(l)['cost_usd'] for l in open(sf)):.2f}" if os.path.exists(sf) else "0")
PB = V.get("predecessor_belief")
if PB:
    put("VPredYes", f"{100 * PB['rebut_believes']:.0f}"); put("VPredNo", f"{100 * PB['rebut_not']:.0f}"); put("VPredN", str(PB["n"])); put("VPredNYes", str(PB["n_believes"]))
    put("VPredCoef", f"{PB['coef']:.2f}"); put("VPredP", fp(PB['p']))
with open(os.path.join(R, "numbers_v2.tex"), "w") as f:
    f.write("% AUTO-GENERATED by code/make_tables_v2.py from results/analysis/v2.json -- do not edit\n")
    for k, v in N.items(): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
json.dump(N, open(os.path.join(R, "results", "analysis", "numbers_v2.json"), "w"), indent=1)
print("v2 tables ok", len(N), "macros")
