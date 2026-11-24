"""Round-2 revision tables and macros from results/analysis/v3.json -> tables/v3_*.tex and numbers_v3.tex.
Macro names: \\W<metric><cond>, e.g. \\WNPlain = rebut rate of newly-true premises (triples, T2) under Plain, primary judge,
all 7 models. Missing cells render as \\pending{}."""
import json, os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
from plotstyle import MODEL_ORDER, PRETTY
from texalign import pad_cols
R = os.path.join(os.path.dirname(__file__), "..")
TD = os.path.join(R, "tables"); os.makedirs(TD, exist_ok=True)
V = json.load(open(os.path.join(R, "results", "analysis", "v3.json")))
T, G, DJ = V["triples"], V["groups"], V["dJ"]
J0 = V["primary"]
PEND = "\\pending{run}"
CONDS = [("plain", "Plain", "Plain"), ("premise", "Premise-check (ours)", "Prem"), ("premise_fq", "Premise-check (FreshQA)", "PremFq"),
         ("date", "Date", "Date"), ("cutoff_date", "Cutoff-stated", "Cut"), ("policy", "Policy (ours)", "Pol"), ("policy_nodate", "\\quad -- no date", "Polnd"),
         ("rag_fresh", "RAG-fresh (oracle)", "Ragf"), ("premise_ragf", "\\quad + premise-check", "PremRagf"), ("rag_mixed_u", "RAG-mixed", "Ragm"), ("rag_stale_u", "RAG-stale", "Rags")]
pc = lambda x: f"{100 * x:.0f}" if x is not None else PEND
def sg(x): return PEND if x is None else (("+" if x >= 0.005 else ("$-$" if x <= -0.005 else "")) + f"{abs(100 * x):.0f}")
def _r(x):
    v = int(round(100 * x)); return ("$-$" if v < 0 else "") + str(abs(v))
def ci(c): return f"[{_r(c[0])},{_r(c[1])}]" if c and c[0] is not None else ""
def fp(p):
    if p is None: return "--"
    return "<.001" if p < 0.001 else (f"{p:.3f}".lstrip("0") if p < 0.01 else f"{p:.2f}".lstrip("0"))

# ---- Table 1 (main): triples, all models, primary judge
n = V["n_triples"]
# 2026-11-20 layout: no \resizebox; gap and CI in separate columns (r@{\,}l) so gaps align on the units digit and CIs on "[";
# p-values in an l column so the decimal points align; units in the headers.
L = [r"\begin{table*}[t]\centering\footnotesize\setlength\tabcolsep{6pt}", r"\begin{tabular}{@{}l ccc c r@{\,}l l r@{\,}l l@{}}", r"\toprule",
     r" & \multicolumn{3}{c}{rebut (\%)} & defer (\%) & \multicolumn{3}{c}{$J_{\text{fam}}$ = \ANC{} $-$ \NEW{}} & \multicolumn{3}{c}{$J_{\text{unf}}$ = \SWP{} $-$ \NEW{}} \\",
     r"\cmidrule(lr){2-4}\cmidrule(lr){5-5}\cmidrule(lr){6-8}\cmidrule(l){9-11}",
     r"Condition & \NEW{} & \ANC{} & \SWP{} & \NEW{} & \multicolumn{2}{c}{pts [95\% CI]} & $p_{\text{model}}$ & \multicolumn{2}{c}{pts [95\% CI]} & $p_{\text{model}}$ \\", r"\midrule"]
for c, name, _ in CONDS:
    t = T.get(f"{J0}|all|{c}")
    if not t: L.append(f"{name} & " + " & ".join([PEND] * 10) + r" \\"); continue
    L.append(f"{name} & {pc(t['rate_P3_NEW'])} & {pc(t['rate_P3_ANC'])} & {pc(t['rate_P3_SWAP'])} & {pc(t['defer_P3_NEW'])} & "
             f"{sg(t.get('Jfam'))} & {{\\footnotesize{ci(t.get('Jfam_ci'))}}} & {fp(t.get('Jfam_model', {}).get('t_p'))} & "
             f"{sg(t.get('Junf'))} & {{\\footnotesize{ci(t.get('Junf_ci'))}}} & {fp(t.get('Junf_model', {}).get('t_p'))} \\\\")
    if c in ("plain", "premise_fq", "policy_nodate"): L.append(r"\midrule")
L += [r"\bottomrule\end{tabular}",
      r"\caption{Matched-triple results (%d triples, %d models, primary judge). $J$: false-minus-true rebuttal margin in percentage points; defer: cannot verify. CIs resample models and entities. Model-level $p$-values are uncorrected; none of the %d tests survives Holm correction.}"
      % (n, len(V["models_all"]), V.get("r3", {}).get("stats", {}).get("table1_n", 0)),
      r"\label{tab:main}\end{table*}"]
pad_cols(L, range(1, 5)); open(os.path.join(TD, "v3_main.tex"), "w").write("\n".join(L) + "\n")

# ---- Table 2: all item groups (main grid, audited), primary judge
# 2026-11-20 layout: single column at \footnotesize without \resizebox; true / false premises as row groups,
# short row labels (the replacement dates are in the caption), numbers right-aligned.
GR = [("NEW_post", "\\NEW{}-post"), ("NEW_near", "\\NEW{}-near"), ("OLD", "\\OLD{}"),
      ("STR_early", "\\STRE{}"), ("STR_late", "\\STRL{}"), ("STALE_POST", "\\STP{}"), ("NEVER", "\\NEV{}")]
GC = [("plain", "Plain"), ("premise", "PC"), ("cutoff_date", "Cut."), ("rag_fresh", "RAG-f"), ("rag_stale_u", "RAG-s")]
T2G = V.get("r3", {}).get("t2_groups", {})
L = [r"\begin{table}[t]\centering\footnotesize\setlength\tabcolsep{2.4pt}", r"\begin{tabular}{@{}l c " + "c" * len(GC) + " cc@{}}", r"\toprule",
     r" & \multicolumn{" + str(len(GC) + 1) + r"}{c}{assigned template} & \multicolumn{2}{c}{T2 only} \\ \cmidrule(lr){2-" + str(len(GC) + 2) + r"}\cmidrule(l){" + str(len(GC) + 3) + "-" + str(len(GC) + 4) + "}",
     r"Premise & $n$ & " + " & ".join(n_ for _, n_ in GC) + r" & $n$ & Plain \\", r"\midrule"]
for k, (g, name) in enumerate(GR):
    if k == 3: L.append(r"\midrule")
    cells = [pc(G.get(f"{J0}|{c}|{g}", {}).get("mean")) for c, _ in GC]
    t2 = T2G.get(g, {})
    L.append(f"{name} & {V['n_items'].get(g, 0)} & " + " & ".join(cells) + f" & {t2.get('n', '--')} & {pc(t2.get('mean'))}" + r" \\")
L += [r"\bottomrule\end{tabular}", r"\caption{Main-grid rebuttals (\%; seven models, primary judge). Top/bottom: true/false premises. Left/right: assigned templates/T2; see Section~\ref{sec:results} for definitions.}", r"\label{tab:groups}\end{table}"]
pad_cols(L, range(1, len(GC) + 4)); open(os.path.join(TD, "v3_groups.tex"), "w").write("\n".join(L) + "\n")

# ---- Table 3: judges on the triples (Plain / PC / Cutoff), incl. cross-family silver
# 2026-11-20 layout: transposed (judges as columns) so it fits one column at \small without \resizebox.
JUD = [("haiku", "Haiku"), ("majority", "Maj."), ("qwen", "Qwen"), ("mistral", "Mistral"), ("silver", "Sonnet"), ("codex", "codex")]
JUD = [(jn, nm) for jn, nm in JUD if T.get(f"{jn}|all|plain")]
def jrow(label, f):
    return label + " & " + " & ".join(f(jn) for jn, _ in JUD) + r" \\"
def tget(jn, c, k, fmt):
    u = T.get(f"{jn}|all|{c}"); return fmt(u.get(k)) if u else "--"
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{3.1pt}", r"\begin{tabular}{@{}l r rrr rr@{}}", r"\toprule",
     r" & \multicolumn{1}{c}{primary} & \multicolumn{3}{c}{other judges} & \multicolumn{2}{c}{held-out} \\ \cmidrule(lr){2-2}\cmidrule(lr){3-5}\cmidrule(l){6-7}",
     " & " + " & ".join(nm for _, nm in JUD) + r" \\", r"\midrule",
     r"\multicolumn{7}{@{}l}{\textit{rebut under Plain (\%)}} \\"]
for k, lab in (("rate_P3_NEW", r"\NEW{}"), ("rate_P3_ANC", r"\ANC{}"), ("rate_P3_SWAP", r"\SWP{}")):
    L.append(jrow(r"\quad " + lab, lambda jn: tget(jn, "plain", k, pc)))
for j, lab in (("Jfam", r"$J_{\text{fam}}$"), ("Junf", r"$J_{\text{unf}}$")):
    L.append(r"\multicolumn{7}{@{}l}{\textit{" + lab + r" (pts)}} \\")
    for c, cn in (("plain", "Plain"), ("premise", "PC"), ("cutoff_date", "Cutoff")):
        L.append(jrow(r"\quad " + cn, lambda jn: tget(jn, c, j, sg)))
L.append(r"\multicolumn{7}{@{}l}{\textit{rebut under RAG-f+PC (\%)}} \\")
L.append(jrow(r"\quad \NEW{}", lambda jn: tget(jn, "premise_ragf", "rate_P3_NEW", pc)))
L += [r"\bottomrule\end{tabular}", r"\caption{Entity-triple results under each labeller (seven models, same responses). Maj.: majority vote; PC: our premise check. The text defines the remaining abbreviations.}", r"\label{tab:judges3}\end{table}"]
open(os.path.join(TD, "v3_judges.tex"), "w").write("\n".join(L) + "\n")

# ---- Table 4: held-out validation (cross-family)
SV = V.get("silver_heldout", {})
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{4pt}", r"\begin{tabular}{@{}l ccc@{}}", r"\toprule", r"Comparison & $n$ & acc. & $\kappa$ \\", r"\midrule"]
if "sonnet_vs_codex" in SV:
    s = SV["sonnet_vs_codex"]; L.append(f"Sonnet 5.5 vs.\\ gpt-5.3-codex & {s['n']} & {s['acc']:.2f} & {s['kappa']:.2f} \\\\"); L.append(r"\midrule")
for jn, name in (("haiku", "Haiku 5.5"), ("majority", "3-judge majority"), ("qwen", "Qwen2.5-7B"), ("mistral", "Mistral-7B")):
    s = SV.get(f"{jn}_vs_consensus")
    if s: L.append(f"{name} vs.\\ consensus & {s['n']} & {s['acc']:.2f} & {s['kappa']:.2f} \\\\")
L.append(r"\midrule")
for key, name in (("ho3|haiku_vs_silver", "Haiku vs.\\ Sonnet (all)"), ("ho3|haiku_vs_codex", "Haiku vs.\\ gpt-5.3-codex (all)"),
                  ("ragf|silver_vs_codex", "RAG-f+PC: Sonnet vs.\\ codex"), ("ragf|haiku_vs_silver", "RAG-f+PC: Haiku vs.\\ Sonnet"), ("ragf|haiku_vs_codex", "RAG-f+PC: Haiku vs.\\ codex")):
    s_ = SV.get(key)
    if s_: L.append(f"{name} & {s_['n']} & {s_['acc']:.2f} & {s_['kappa']:.2f} \\\\")
L += [r"\bottomrule\end{tabular}", r"\caption{Held-out label agreement on entity triples. Consensus uses only responses where both held-out labellers agree; \emph{All} uses every available label. The last three rows assess \textsc{RAG-fresh+PC}.}", r"\label{tab:heldout}\end{table}"]
pad_cols(L, range(1, 4)); open(os.path.join(TD, "v3_heldout.tex"), "w").write("\n".join(L) + "\n")

# ---- Table: per model, triples (primary judge)
PMR = V["per_model_triples"]
SEL = [("plain", "Plain"), ("premise", "PC"), ("cutoff_date", "Cutoff"), ("rag_fresh", "RAG-f"), ("premise_ragf", "RAG-f+PC"), ("rag_stale_u", "RAG-s")]
L = [r"\begin{table*}[t]\centering\small\setlength\tabcolsep{3.1pt}", r"\begin{tabular}{@{}l " + r"@{\hspace{10pt}}".join(["ccc"] * len(SEL)) + "@{}}", r"\toprule",
     " & " + " & ".join(f"\\multicolumn{{3}}{{c}}{{{nm}}}" for _, nm in SEL) + r" \\",
     "".join(f"\\cmidrule({'lr' if k < len(SEL) - 1 else 'l'}){{{2 + 3 * k}-{4 + 3 * k}}}" for k in range(len(SEL))),
     "Model & " + " & ".join(["N & F & S"] * len(SEL)) + r" \\", r"\midrule"]
for m in [x for x in MODEL_ORDER if any(k.startswith(x + "|") for k in PMR)]:
    cells = []
    for c, _ in SEL:
        d = PMR.get(f"{m}|{c}")
        cells += [pc(d["P3_NEW"]), pc(d["P3_ANC"]), pc(d["P3_SWAP"])] if d else ["--"] * 3
    L.append(f"{PRETTY[m]} & " + " & ".join(cells) + r" \\")
L += [r"\bottomrule\end{tabular}", r"\caption{Per-model rebuttal rates (\%) on entity triples, primary judge. N/F/S: \NEW{}/\ANC{}/\SWP{}. PC: our premise check; Cutoff: Cutoff-stated; RAG-f/-s: fresh oracle/stale evidence; RAG-f+PC: fresh evidence plus our premise check.}", r"\label{tab:permodel3}\end{table*}"]
pad_cols(L, range(1, 3 * len(SEL) + 1)); open(os.path.join(TD, "v3_permodel.tex"), "w").write("\n".join(L) + "\n")

# ---- Table: scale-up models (GX10), per model and pooled
LG = V.get("large", {}); LM = V.get("large_models", [])
PRET = dict(PRETTY, **{"qwen2.5-14b": "Qwen2.5-14B", "qwen2.5-32b": "Qwen2.5-32B", "phi4": "Phi-4 (14B)"})
if LM:
    COLS = [("plain", "NEW_post"), ("plain", "OLD"), ("plain", "P3_NEW"), ("plain", "P3_ANC"), ("plain", "P3_SWAP"), ("premise", "P3_NEW"),
            ("cutoff_date", "P3_NEW"), ("rag_fresh", "P3_NEW"), ("premise_ragf", "P3_NEW"), ("rag_stale_u", "P3_NEW")]
    # 2026-11-20 layout: transposed (models as columns) so the table fits one column at \small.
    HD = {"qwen2.5-14b": ("Qwen2.5", "14B"), "phi4": ("Phi-4", "14B"), "qwen2.5-32b": ("Qwen2.5", "32B"), "pooled": ("Pooled", "(%d)" % len(LM))}
    MS = LM + ["pooled"]
    RL = [(None, r"\textit{Plain, main grid}"), (0, r"\quad \NEW{}-post"), (1, r"\quad \OLD{}"),
          (None, r"\textit{Plain, entity triples}"), (2, r"\quad \NEW{} (true)"), (3, r"\quad \ANC{}"), (4, r"\quad \SWP{}"),
          (None, r"\textit{rebut \NEW{}, entity triples}"), (5, r"\quad Premise-check"), (6, r"\quad Cutoff-stated"), (7, r"\quad RAG-fresh"),
          (8, r"\quad RAG-fresh+PC"), (9, r"\quad RAG-stale")]
    L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{4pt}", r"\begin{tabular}{@{}l " + "c" * len(LM) + " c@{}}", r"\toprule",
         " & " + " & ".join(HD.get(m, (PRET.get(m, m), ""))[0] for m in MS) + r" \\",
         r"Rebuttals (\%) & " + " & ".join(HD.get(m, ("", ""))[1] for m in MS) + r" \\", r"\midrule"]
    for ci_, lab in RL:
        if ci_ is None: L.append(r"\multicolumn{%d}{@{}l}{%s} \\" % (len(MS) + 1, lab)); continue
        c, k = COLS[ci_]
        L.append(lab + " & " + " & ".join(pc(LG.get(f"{m}|{c}", {}).get(k)) for m in MS) + r" \\")
    L += [r"\bottomrule\end{tabular}",
          r"\caption{Rebuttal rates (\%) for three larger models, scored by the primary judge. Prompts and greedy decoding match the small-model study; these models are pooled separately.}",
          r"\label{tab:large}\end{table}"]
    pad_cols(L, range(1, len(MS) + 1)); open(os.path.join(TD, "v3_large.tex"), "w").write("\n".join(L) + "\n")

# ---- macros
N = {}
def put(k, v): N[k] = v
for c, _, tag in CONDS:
    t = T.get(f"{J0}|all|{c}") or {}
    for k, nm in (("rate_P3_NEW", "WN"), ("rate_P3_ANC", "WA"), ("rate_P3_SWAP", "WS"), ("defer_P3_NEW", "WDefN"), ("accept_P3_NEW", "WAccN")):
        put(f"{nm}{tag}", pc(t.get(k)))
    for j in ("Jfam", "Junf"):
        put(f"W{j}{tag}", sg(t.get(j))); put(f"W{j}{tag}CI", ci(t.get(f"{j}_ci")) or PEND)
        m = t.get(f"{j}_model", {}); put(f"W{j}{tag}P", fp(m.get("t_p"))); put(f"W{j}{tag}Pos", str(m.get("n_pos", "--")))
    if c != "plain":
        for j in ("Jfam", "Junf", "dNEW"):
            d = DJ.get(f"{J0}|{c}|{j}")
            if d: put(f"WD{j}{tag}", sg(d["mean"])); put(f"WD{j}{tag}CI", ci(d["ci"])); put(f"WD{j}{tag}P", fp(d["model"].get("t_p")))
    for jn, jt in (("majority", "Maj"), ("qwen", "Q"), ("mistral", "M"), ("silver", "Sil"), ("codex", "Cx")):
        u = T.get(f"{jn}|all|{c}")
        if u:
            put(f"WJ{jt}N{tag}", pc(u["rate_P3_NEW"])); put(f"WJ{jt}A{tag}", pc(u["rate_P3_ANC"])); put(f"WJ{jt}S{tag}", pc(u["rate_P3_SWAP"]))
            put(f"WJ{jt}Jfam{tag}", sg(u.get("Jfam"))); put(f"WJ{jt}Junf{tag}", sg(u.get("Junf")))
    for g, gt in (("NEW_post", "New"), ("NEW_near", "Near"), ("OLD", "Old"), ("STR_early", "Stre"), ("STR_late", "Strl"), ("STALE_POST", "Stp"), ("NEVER", "Nev")):
        d = G.get(f"{J0}|{c}|{g}")
        if d: put(f"WG{gt}{tag}", pc(d["mean"])); put(f"WG{gt}{tag}CI", ci(d["ci"]))
    m = G.get(f"{J0}|{c}|new_minus_old_model")
    if m: put(f"WGapOld{tag}P", fp(m["t_p"])); put(f"WGapOld{tag}Pos", str(m["n_pos"]))
put("WNTri", str(n)); put("WNModels", str(len(V["models_all"])))
for g, gt in (("NEW_post", "New"), ("NEW_near", "Near"), ("OLD", "Old"), ("STR_early", "Stre"), ("STR_late", "Strl"), ("STALE_POST", "Stp"), ("NEVER", "Nev")):
    put(f"WNG{gt}", str(V["n_items"].get(g, 0)))
ps = V["person_sitelinks_median"]; put("WSlN", f"{ps['P3_NEW']:.0f}"); put("WSlA", f"{ps['P3_ANC']:.0f}"); put("WSlS", f"{ps['P3_SWAP']:.0f}")
EA = V["error_analysis"]
if EA.get("n"):
    put("WEaN", str(EA["n"]))
    for k, nm in (("cutoff_mention", "WEaCut"), ("invented_tenure", "WEaInv"), ("names_predecessor", "WEaPred"), ("unfamiliar", "WEaUnf")):
        put(nm, f"{100 * EA.get(k, 0) / EA['n']:.0f}")
PF = V["premise_formula_by_model"]
for m, tag in (("qwen2.5-3b", "QThree"), ("smollm2-1.7b", "Smol"), ("qwen2.5-0.5b", "QHalf"), ("qwen2.5-1.5b", "QOneFive")):
    if m in PF: put(f"WForm{tag}", f"{100 * PF[m]:.0f}")
if "sonnet_vs_codex" in SV:
    put("WSvCAcc", f"{SV['sonnet_vs_codex']['acc']:.2f}"); put("WSvCKappa", f"{SV['sonnet_vs_codex']['kappa']:.2f}"); put("WSvCN", str(SV["sonnet_vs_codex"]["n"]))
    put("WConsN", str(SV.get("consensus_n", 0)))
    for jn, jt in (("haiku", "H"), ("majority", "Maj"), ("qwen", "Q"), ("mistral", "M")):
        s = SV.get(f"{jn}_vs_consensus")
        if s: put(f"WCons{jt}Acc", f"{s['acc']:.2f}"); put(f"WCons{jt}Kappa", f"{s['kappa']:.2f}")
uf = os.path.join(R, "results", "labels", "openai-gpt-5.3-codex", "usage.log")
if os.path.exists(uf):
    tok = [json.loads(l) for l in open(uf)]
    put("WCodexIn", f"{sum(t['input'] for t in tok) / 1e6:.2f}"); put("WCodexOut", f"{sum(t['output'] for t in tok) / 1e6:.2f}"); put("WCodexN", f"{sum(t['n'] for t in tok):,}".replace(",", "{,}"))
for m, tag in (("pooled", "Pool"), ("qwen2.5-14b", "QFourteen"), ("phi4", "PhiFour"), ("qwen2.5-32b", "QThirtyTwo")):
    for c, ct in (("plain", "Plain"), ("premise", "Prem"), ("cutoff_date", "Cut"), ("rag_fresh", "Ragf"), ("premise_ragf", "PremRagf"), ("rag_stale_u", "Rags")):
        d = LG.get(f"{m}|{c}")
        if d:
            put(f"WL{tag}N{ct}", pc(d.get("P3_NEW"))); put(f"WL{tag}A{ct}", pc(d.get("P3_ANC"))); put(f"WL{tag}S{ct}", pc(d.get("P3_SWAP")))
            put(f"WL{tag}Jfam{ct}", sg(d.get("Jfam"))); put(f"WL{tag}Jfam{ct}CI", ci(d.get("Jfam_ci")))
            put(f"WL{tag}New{ct}", pc(d.get("NEW_post"))); put(f"WL{tag}Old{ct}", pc(d.get("OLD")))
put("WNLarge", str(len(LM)))
# ======== round 3: robustness table and macros (from v3.json["r3"])
R3 = V.get("r3", {})
def tp(d, j):
    m = (d or {}).get(f"{j}_model", {}); return fp(m.get("t_p")) if m else "--"
def Jc(d, j): return f"{sg(d.get(j))} & {{\\footnotesize{ci(d.get(j + '_ci'))}}}" if d and d.get(j) is not None else r"\multicolumn{2}{c}{--}"
def tri_row(name, ms, d, ntri=None):
    return (f"{name} & {ms} & {ntri if ntri is not None else d.get('n_triples', '--')} & {pc(d.get('P3_NEW'))} & {pc(d.get('P3_ANC'))} & {pc(d.get('P3_SWAP'))} & "
            f"{Jc(d, 'Jfam')} & {tp(d, 'Jfam')} & {Jc(d, 'Junf')} & {tp(d, 'Junf')} \\\\")
def from_T(key):
    t = T.get(key)
    if not t: return {}
    return dict(P3_NEW=t["rate_P3_NEW"], P3_ANC=t["rate_P3_ANC"], P3_SWAP=t["rate_P3_SWAP"], Jfam=t.get("Jfam"), Jfam_ci=t.get("Jfam_ci"), Jfam_model=t.get("Jfam_model"),
                Junf=t.get("Junf"), Junf_ci=t.get("Junf_ci"), Junf_model=t.get("Junf_model"), n_triples=n)
HG, SW, LT = R3.get("hedge", {}), R3.get("swap", {}), R3.get("long_triples", {})
rows = [("Primary analysis", "7", from_T(f"{J0}|all|plain")), ("Four knowledgeable models", "4", from_T(f"{J0}|know|plain")),
        ("\\quad same models, 256 tokens", str(len(LT.get("models", []))), LT.get("long", {})),
        ("Unhedged rebuttals only", "7", HG.get("haiku|unhedged|all|plain", {})), ("Hedged rebuttals only", "7", HG.get("haiku|hedged|all|plain", {})),
        ("\\SWP{} no more popular than \\NEW{}", "7", SW.get("swap_le_new|all", {})),
        ("\\SWP{} nationality-compatible", "7", SW.get("compatible|all", {})),
        ("\\SWP{} not nationality-compatible", "7", SW.get("incompatible|all", {})),
        ("Held-out labeller: Sonnet 5.5", "7", from_T("silver|all|plain")), ("Held-out labeller: gpt-5.3-codex", "7", from_T("codex|all|plain"))]
# 2026-11-20 layout: \small, gap and CI in separate columns (CI no longer \scriptsize), decimal-aligned p-values.
L = [r"\begin{table*}[t]\centering\footnotesize\setlength\tabcolsep{4.4pt}", r"\begin{tabular}{@{}l cc ccc r@{\,}l l r@{\,}l l@{}}", r"\toprule",
     r" & & & \multicolumn{3}{c}{rebut (\%)} & \multicolumn{3}{c}{$J_{\text{fam}}$ (pts)} & \multicolumn{3}{c}{$J_{\text{unf}}$ (pts)} \\",
     r"\cmidrule(lr){4-6}\cmidrule(lr){7-9}\cmidrule(l){10-12}",
     r"\textsc{Plain}, entity triples & models & triples & \NEW{} & \ANC{} & \SWP{} & \multicolumn{2}{c}{pts [95\% CI]} & $p_{t}$ & \multicolumn{2}{c}{pts [95\% CI]} & $p_{t}$ \\", r"\midrule"]
for k, (name, ms, d) in enumerate(rows):
    if d: L.append(tri_row(name, ms, d))
    if k in (2, 4, 7): L.append(r"\midrule")
LP = LG.get("pooled|plain")
if LP:
    L.append(r"\midrule")
    L.append(tri_row("Larger models (14--32B)", str(len(LM)), dict(P3_NEW=LP["P3_NEW"], P3_ANC=LP["P3_ANC"], P3_SWAP=LP["P3_SWAP"], Jfam=LP["Jfam"], Jfam_ci=LP["Jfam_ci"], Junf=LP["Junf"], Junf_ci=LP["Junf_ci"]), n))
L += [r"\bottomrule\end{tabular}",
      r"\caption{Robustness of the \textsc{Plain} margins (primary judge unless stated). Hedged and unhedged rows partition rebuttals; popularity and nationality rows restrict the controls. CIs resample models and entities; $p_t$ tests per-model margins. Section~\ref{sec:analysis} defines the checks.}",
      r"\label{tab:robust}\end{table*}"]
pad_cols(L, range(1, 6)); open(os.path.join(TD, "v3_robust.tex"), "w").write("\n".join(L) + "\n")

def putJ(prefix, d):
    if not d: return
    for k, nm in (("P3_NEW", "N"), ("P3_ANC", "A"), ("P3_SWAP", "S")): put(f"{prefix}{nm}", pc(d.get(k)))
    for j in ("Jfam", "Junf"):
        if d.get(j) is None: continue
        put(f"{prefix}{j}", sg(d[j])); put(f"{prefix}{j}CI", ci(d.get(f"{j}_ci")))
        m = d.get(f"{j}_model") or {}
        if m.get("t_p") is not None: put(f"{prefix}{j}P", fp(m["t_p"])); put(f"{prefix}{j}W", fp(m.get("wilcoxon_p"))); put(f"{prefix}{j}Pos", str(m.get("n_pos")))
    if "n_triples" in d: put(f"{prefix}NTri", str(d["n_triples"]))
# Wilcoxon / positives for Table-1 J's
for c, _, tag in CONDS:
    t = T.get(f"{J0}|all|{c}") or {}
    for j in ("Jfam", "Junf"):
        m = t.get(f"{j}_model", {})
        if m: put(f"W{j}{tag}W", fp(m.get("wilcoxon_p")))
    for j in ("Jfam", "Junf", "dNEW"):
        d = DJ.get(f"{J0}|{c}|{j}")
        if d and c != "plain": put(f"WD{j}{tag}W", fp(d["model"].get("wilcoxon_p"))); put(f"WD{j}{tag}Pos", str(d["model"].get("n_pos")))
putJ("WKn", from_T(f"{J0}|know|plain"))
ST = R3.get("stats", {})
if ST:
    put("WJfamPlainHolm", fp(ST["plain_holm"][0])); put("WJunfPlainHolm", fp(ST["plain_holm"][1]))
    put("WTabOneN", str(ST["table1_n"])); put("WTabOneMinHolm", fp(ST["table1_min_holm"])); put("WTabOneNSigHolm", str(ST["table1_n_sig_holm"]))
    for jn, jt in (("silver", "Sil"), ("codex", "Cx")):
        if f"{jn}_plain_p" in ST: put(f"WJ{jt}JfamPlainP", fp(ST[f"{jn}_plain_p"][0])); put(f"WJ{jt}JunfPlainP", fp(ST[f"{jn}_plain_p"][1]))
    put("WNZero", str(ST["n_zero_models_plain"])); put("WGapOldPlainW", fp(ST["new_old_w"]))
DS = R3.get("defer_split", {})
for c, tag in (("plain", "Plain"), ("cutoff_date", "Cut"), ("rag_fresh", "Ragf")):
    if c in DS: put(f"WDefRefN{tag}", pc(DS[c]["refuse"])); put(f"WDefCvN{tag}", pc(DS[c]["cannot_verify"]))
for hk, ht in (("unhedged", "Uh"), ("hedged", "Hd")):
    putJ(f"W{ht}", HG.get(f"haiku|{hk}|all|plain")); putJ(f"W{ht}Kn", HG.get(f"haiku|{hk}|know|plain"))
    putJ(f"W{ht}Cut", HG.get(f"haiku|{hk}|all|cutoff_date"))
    for jn, jt in (("silver", "Sil"), ("codex", "Cx")): putJ(f"W{ht}{jt}", HG.get(f"{jn}|{hk}|all|plain"))
for arm, nm in (("P3_NEW", "N"), ("P3_ANC", "A"), ("P3_SWAP", "S")):
    d = HG.get(f"share_hedged|{arm}")
    if d and d["share"] is not None: put(f"WHgShare{nm}", pc(d["share"]))
RP = R3.get("ragf_pc", {})
if RP:
    put("WRpMedN", pc(RP["median_new"])); putJ("WRpKn", RP["know"]); putJ("WRpKnPlain", RP["know_plain"])
    for m, tag in (("qwen2.5-0.5b", "QHalf"), ("qwen2.5-1.5b", "QOneFive"), ("smollm2-1.7b", "Smol"), ("qwen2.5-3b", "QThree"), ("phi3.5-mini", "Phi"), ("qwen2.5-7b", "QSeven"), ("mistral-7b", "Mis")):
        put(f"WRpN{tag}", pc(RP["per_model_new"].get(m)))
    rt = RP["rebuttal_text"]; put("WRpReb", str(rt.get("n", 0))); put("WRpForm", str(rt.get("formula", 0))); put("WRpInsuff", str(rt.get("evidence_insufficient", 0)))
    put("WRpInsuffSmall", str(rt.get("insufficient_small_qwen", 0)))
    put("WRpSmallQwen", str(RP["rebuttals_by_model"].get("qwen2.5-0.5b", 0) + RP["rebuttals_by_model"].get("qwen2.5-1.5b", 0) + RP["rebuttals_by_model"].get("qwen2.5-3b", 0)))
    for jn, jt in (("silver", "Sil"), ("codex", "Cx")):
        if jn in RP: put(f"WRp{jt}N", pc(RP[jn]["rate_P3_NEW"]))
        if f"{jn}_know" in RP: put(f"WRp{jt}KnN", pc(RP[f"{jn}_know"]["rate_P3_NEW"]))
for key, tag in (("ragf|silver_vs_codex", "RagfSC"), ("ragf|haiku_vs_silver", "RagfHS"), ("ragf|haiku_vs_codex", "RagfHC"), ("ho3|haiku_vs_silver", "HS"), ("ho3|haiku_vs_codex", "HC")):
    s_ = SV.get(key)
    if s_: put(f"WHo{tag}N", str(s_["n"])); put(f"WHo{tag}Acc", f"{s_['acc']:.2f}"); put(f"WHo{tag}Kappa", f"{s_['kappa']:.2f}")
LV = R3.get("large_vs_know", {})
if LV:
    put("WKnNewPlain", pc(LV["know|plain"]["NEW_post"])); put("WKnOldPlain", pc(LV["know|plain"]["OLD"])); put("WKnOldPrem", pc(LV["know|premise"]["OLD"]))
    for m, tag in (("phi3.5-mini", "Phi"), ("qwen2.5-7b", "QSeven"), ("qwen2.5-3b", "QThree"), ("mistral-7b", "Mis")):
        d = LV.get(f"{m}|plain")
        if d: put(f"WSm{tag}NewPlain", pc(d["NEW_post"])); put(f"WSm{tag}NPlain", pc(d["P3_NEW"]))
    d = LV.get("qwen2.5-7b|cutoff_date")
    if d: put("WSmQSevenNCut", pc(d["P3_NEW"]))
LP = LG.get("pooled|plain", {})
if LP:
    put("WLPoolJunfPlain", sg(LP["Junf"])); put("WLPoolJunfPlainCI", ci(LP["Junf_ci"]))
for m, tag in (("qwen2.5-14b", "QFourteen"), ("phi4", "PhiFour"), ("qwen2.5-32b", "QThirtyTwo")):
    d = LG.get(f"{m}|premise")
    if d: put(f"WL{tag}OldPrem", pc(d.get("OLD")))
d = LG.get("pooled|premise")
if d: put("WLPoolOldPrem", pc(d.get("OLD")))
if SW:
    for c, nm in (("P3_SWAP", "S"), ("P3_ANC", "A"), ("P3_NEW", "N")):
        d = SW.get(f"spearman|{c}")
        if d: put(f"WSwRho{nm}", f"{d['rho']:.2f}"); put(f"WSwRho{nm}P", fp(d["p"]))
    put("WSwMoreFam", str(SW.get("n_swap_more_famous"))); put("WSwAMoreFam", str(SW.get("n_former_more_famous")))
    putJ("WSwLe", SW.get("swap_le_new|all")); putJ("WSwLeKn", SW.get("swap_le_new|know"))
    putJ("WSwComp", SW.get("compatible|all")); putJ("WSwCompKn", SW.get("compatible|know"))
    putJ("WSwInc", SW.get("incompatible|all")); putJ("WSwIncKn", SW.get("incompatible|know"))
    for sn, st in (("all", ""), ("know", "Kn")):
        l_ = SW.get(f"lpm|{sn}")
        if l_:
            for k, nm in (("Jfam_adj", "Jfam"), ("Junf_adj", "Junf")):
                put(f"WSwLpm{st}{nm}", sg(l_[k]["coef"])); put(f"WSwLpm{st}{nm}CI", ci(l_[k]["ci"])); put(f"WSwLpm{st}{nm}P", fp(l_[k]["p"]))
            put(f"WSwLpm{st}Px", f"{100 * l_['lpx']['coef']:.1f}"); put(f"WSwLpm{st}PxP", fp(l_["lpx"]["p"]))
TG = R3.get("t2_groups", {})
for g, gt in (("NEW_post", "New"), ("NEW_near", "Near"), ("OLD", "Old"), ("STR_early", "Stre"), ("STR_late", "Strl"), ("STALE_POST", "Stp"), ("NEVER", "Nev")):
    if g in TG and TG[g]["mean"] is not None: put(f"WTt{gt}", pc(TG[g]["mean"])); put(f"WTt{gt}N", str(TG[g]["n"])); put(f"WTt{gt}CI", ci(TG[g]["ci"]))
if "new_minus_old_model" in TG:
    put("WTtGapP", fp(TG["new_minus_old_model"]["t_p"])); put("WTtGapW", fp(TG["new_minus_old_model"]["wilcoxon_p"])); put("WTtGapPos", str(TG["new_minus_old_model"]["n_pos"]))
if LT:
    putJ("WLgS", LT["short"]); putJ("WLgL", LT["long"]); putJ("WLgLUh", LT.get("long_unhedged")); put("WLgSame", pc(LT["same_label"])); put("WLgN", str(LT["n"])); put("WLgM", str(len(LT["models"])))
Q = R3.get("qwen35", {})
for k, nm in (("plain|NEW_post", "WQtfNew"), ("plain|OLD", "WQtfOld"), ("plain|STR_early", "WQtfStre"), ("plain|NEW_2025", "WQtfNewTwentyFive"), ("plain|NEW_2026", "WQtfNewTwentySix"), ("premise|NEW_post", "WQtfNewPrem"), ("policy|NEW_post", "WQtfNewPol")):
    if k in Q: put(nm, pc(Q[k]))
IT = R3.get("invented_tenure_strict")
if IT and IT["n"]: put("WEaInvStrict", f"{100 * IT['k'] / IT['n']:.0f}")
put("WJanTri", str(R3.get("jan1_new_triples", 0))); put("WJanPost", str(R3.get("jan1_new_post", 0)))
put("WDefNRagf", pc(T.get(f"{J0}|all|rag_fresh", {}).get("defer_P3_NEW")))
put("WAccNRagf", pc(T.get(f"{J0}|all|rag_fresh", {}).get("accept_P3_NEW")))
hk = os.path.join(R, "results", "labels", "claude-haiku-5-5", "usage.log")
if os.path.exists(hk): put("WHaikuCost", f"{sum(json.loads(l)['cost_usd'] for l in open(hk)):.2f}")
sk = os.path.join(R, "results", "labels", "silver-claude-sonnet-5-5", "usage.log")
if os.path.exists(sk): put("WSonnetCost", f"{sum(json.loads(l)['cost_usd'] for l in open(sk)):.2f}")
# Sonnet held-out labelling: items re-asked with a reasoning budget (usage-log runs on a keys file with >20 output tokens per
# item are the --retry runs; letter-only runs use <8) and items still unlabelled
if os.path.exists(sk):
    ul = [json.loads(l) for l in open(sk)]
    put("WSilRetry", str(sum(u["n"] for u in ul if u.get("keys") and u["output"] / max(1, u["n"]) > 20)))
    keys_all = set()
    for kf in ("keys_v3.json", "keys_v3_ragf.json"):
        fk = os.path.join(R, "results", "labels", "heldout", kf)
        if os.path.exists(fk): keys_all |= {tuple(k) for k in json.load(open(fk))}
    got = {tuple(json.loads(l)["key"]) for l in open(os.path.join(R, "results", "labels", "silver-claude-sonnet-5-5", "silver_v3.jsonl"))}
    put("WSilMissing", str(len(keys_all - got))); put("WHoKeys", f"{len(keys_all):,}".replace(",", "{,}"))
with open(os.path.join(R, "numbers_v3.tex"), "w") as f:
    f.write("% AUTO-GENERATED by code/make_tables_v3.py from results/analysis/v3.json -- do not edit\n")
    for k, v in N.items(): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
json.dump(N, open(os.path.join(R, "results", "analysis", "numbers_v3.json"), "w"), indent=1)
print("v3 tables ok", len(N), "macros")
