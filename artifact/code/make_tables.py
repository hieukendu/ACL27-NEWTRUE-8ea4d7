"""LaTeX tables (tables/*.tex) and number macros (numbers.tex) from results/analysis/*.json."""
import json, os, sys, glob
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from texalign import pad_cols
from plotstyle import MODEL_ORDER, PRETTY
R = os.path.join(os.path.dirname(__file__), "..")
TD = os.path.join(R, "tables"); os.makedirs(TD, exist_ok=True)
M = json.load(open(os.path.join(R, "results", "analysis", "main.json")))
CUT = json.load(open(os.path.join(R, "results", "analysis", "cutoffs.json")))
P, T, TESTS = M["pooled"], M["table"], M["tests"]
CONDS = ["plain", "premise", "date", "rag_fresh", "rag_stale", "policy", "policy_nodate"]
SHORT = {"plain": "Plain", "premise": "Premise-check", "date": "Date", "rag_fresh": "RAG-fresh", "rag_stale": "RAG-stale",
         "policy": "Policy (ours)", "policy_nodate": "\\quad -- no date"}
pc = lambda d: f"{100 * d['mean']:.0f}" if d and d.get("mean") is not None else "--"
pci = lambda d: f"{100 * d['mean']:.0f} {{\\scriptsize[{100 * d['ci'][0]:.0f},{100 * d['ci'][1]:.0f}]}}"
models = [m for m in MODEL_ORDER if m in M["models"]]
sig = {(t["model"], t["cond"], t["metric"]): t for t in TESTS}

# Table: pooled. Main block: models with an identified cutoff (a-priori subset); right block: all models.
PID = M["pooled_id"]
L = [r"\begin{table*}[t]\centering\small\setlength\tabcolsep{3.6pt}", r"\begin{tabular}{l cccccc c ccc}", r"\toprule",
     r" & \multicolumn{7}{c}{\textbf{Models with an identified cutoff} (%d)} & \multicolumn{3}{c}{\textbf{All models} (%d)} \\" % (len(M["id_models"]), len(M["full_models"])),
     r"\cmidrule(lr){2-8}\cmidrule(lr){9-11}",
     r" & \multicolumn{2}{c}{rebut true ($\downarrow$)} & \multicolumn{2}{c}{rebut false ($\uparrow$)} & defer & \STP{} & & rebut & rebut & \\",
     r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
     r"Condition & \NEW{}-post & \OLD{} & \NEV{} & \STR{} & \NEW{}-post & accept & $J_{\text{new}}$ & \NEW{}-post & \NEV{} & $J_{\text{new}}$ \\", r"\midrule"]
for c in CONDS:
    J = M["discrimination"][f"{c}|new"]
    L.append(f"{SHORT[c]} & {pci(PID[f'{c}|NEW_post|rebut'])} & {pc(PID[f'{c}|OLD|rebut'])} & {pci(PID[f'{c}|NEVER|rebut'])} & {pc(PID[f'{c}|STALE_PRE|rebut'])} & "
             f"{pc(PID[f'{c}|NEW_post|cannot_verify'])} & {pc(PID[f'{c}|STALE_POST|accept'])} & {pc(PID[f'{c}|J_new'])} & "
             f"{pc(P[f'{c}|NEW_post|rebut'])} & {pc(P[f'{c}|NEVER|rebut'])} & {pc(J)} \\\\")
    if c in ("plain", "date", "rag_stale"): L.append(r"\midrule")
L += [r"\bottomrule\end{tabular}",
      r"\caption{Response rates (\%%) pooled over models, item-cluster bootstrap 95\%% CIs in brackets. Left: the %d models whose effective cutoff the date probe identifies (%s); this subset is fixed by the probe alone (\S\ref{sec:cutoffs}). Right: all %d models that ran every condition. \emph{Defer} = cannot verify. $J_{\text{new}}$ = rebut(\NEV{}) $-$ rebut(\NEW{}-post): how much more often a never-true premise is rebutted than a newly-true one (0 = no discrimination). Qwen2.5-7B judge.}" % (len(M["id_models"]), ", ".join(PRETTY[m] for m in M["id_models"]), len(M["full_models"])),
      r"\label{tab:pooled}\end{table*}"]
open(os.path.join(TD, "pooled.tex"), "w").write("\n".join(L) + "\n")

# Table: per model
def cell(m, c):
    x, y = T.get(f"{m}|{c}|NEW_post|rebut"), T.get(f"{m}|{c}|NEVER|rebut")
    if not x or x["mean"] is None: return "--", "--"
    sx = sig.get((m, c, "FRR_new")); sy = sig.get((m, c, "catch_never"))
    mx = "$^{*}$" if sx and sx["p_holm"] < 0.05 else ""
    my = "$^{*}$" if sy and sy["p_holm"] < 0.05 else ""
    return pc(x) + mx, pc(y) + my
SEL = ["plain", "premise", "rag_fresh", "rag_stale", "policy"]
L = [r"\begin{table*}[t]\centering\small\setlength\tabcolsep{3.2pt}", r"\begin{tabular}{l c " + " ".join(["cc"] * len(SEL)) + "}", r"\toprule",
     r" & est. & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{SHORT[c].replace(' (ours)', '')}}}" for c in SEL) + r" \\",
     "".join(f"\\cmidrule(lr){{{3 + 2 * k}-{4 + 2 * k}}}" for k in range(len(SEL))),
     r"Model & cutoff & " + " & ".join(["FRR$\\downarrow$ & catch$\\uparrow$"] * len(SEL)) + r" \\", r"\midrule"]
for m in models:
    cu = CUT.get(m, {})
    ok = cu.get("perm_p", 1) < 0.05 and cu.get("p_before", 0) > cu.get("p_after", 1)
    cut = cu["cutoff"] if ok else "n.i."
    cells = []
    for c in SEL: cells += list(cell(m, c))
    L.append(f"{PRETTY[m]} & {cut} & " + " & ".join(cells) + r" \\")
L += [r"\bottomrule\end{tabular}",
      r"\caption{Per-model false-rebuttal rate on \NEW{}-post true premises (FRR, $n{=}%d$ items) and catch rate on \NEV{} false premises ($n{=}%d$), in \%%. $^{*}$: differs from \textsc{Plain} by an exact McNemar test, Holm-corrected over all %d tests ($p<.05$). Est.\ cutoff: change point of the date probe (\S\ref{sec:cutoffs}); n.i.\ = not identifiable (permutation $p\ge.05$ or no downward step). --: condition not run.}"
      % (M["n_items"]["NEW_post"], M["n_items"]["NEVER"], len(TESTS)), r"\label{tab:permodel}\end{table*}"]
open(os.path.join(TD, "permodel.tex"), "w").write("\n".join(L) + "\n")

# Table: relation breakdown
B = M["breakdowns"]
RELS = ["head of gov.", "head of state", "CEO", "head coach", "chairperson"]
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{3.5pt}", r"\begin{tabular}{l ccc ccc}", r"\toprule",
     r" & \multicolumn{3}{c}{FRR \NEW{}-post} & \multicolumn{3}{c}{catch \NEV{}+\STR{}} \\ \cmidrule(lr){2-4}\cmidrule(lr){5-7}",
     r"Relation & Plain & PC & Pol & Plain & PC & Pol \\", r"\midrule"]
for r in RELS:
    row = []
    for g in ("NEW", "FALSE"):
        for c in ("plain", "premise", "policy"):
            d = B.get(f"rel|{c}|{g}", {}).get(r); row.append(pc(d) if d else "--")
    n = B.get(f"rel|plain|NEW", {}).get(r, {}).get("n", 0) // max(1, len(M["full_models"]))
    L.append(f"{r} ({n}) & " + " & ".join(row) + r" \\")
L += [r"\bottomrule\end{tabular}", r"\caption{Rates (\%) by relation, pooled over models. The number of \NEW{}-post items is in parentheses. PC = Premise-check, Pol = Policy.}", r"\label{tab:relation}\end{table}"]
open(os.path.join(TD, "relation.tex"), "w").write("\n".join(L) + "\n")

# Table: judge agreement & robustness (3 judges + rules; headline replicated under each labeller)
A = M["agreement"]; ALT = M["alt_labeler"]
f2 = lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else "--"
fmtn = lambda n: f"{n:,}".replace(",", "{,}")
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{3pt}", r"\begin{tabular}{lrc}", r"\toprule", r"Labellers compared & $n$ & $\kappa$ \\", r"\midrule",
     f"Qwen2.5-7B vs.\\ Mistral-7B & {fmtn(A['n_subset'])} & {f2(A['kappa_qwen_mistral'])} \\\\",
     f"Qwen2.5-7B vs.\\ Claude Haiku 5.5 & {fmtn(A.get('n_haiku', 0))} & {f2(A.get('kappa_qwen_haiku'))} \\\\",
     f"Mistral-7B vs.\\ Claude Haiku 5.5 & {fmtn(A.get('n_mistral_haiku', 0))} & {f2(A.get('kappa_mistral_haiku'))} \\\\",
     f"Qwen2.5-7B vs.\\ 3-judge majority & {fmtn(A.get('n_majority', 0))} & {f2(A.get('kappa_qwen_majority'))} \\\\",
     f"Qwen2.5-7B vs.\\ rules & {fmtn(A['n_all'])} & {f2(A['kappa_qwen_rules_all'])} \\\\",
     f"Claude Haiku 5.5 vs.\\ rules & {fmtn(A.get('n_haiku', 0))} & {f2(A.get('kappa_haiku_rules'))} \\\\",
     r"\bottomrule\end{tabular}"]
# headline replication: identified-cutoff models, metric rows x labeller columns
L += [r"\vspace{4pt}", r"\begin{tabular}{l cccc}", r"\toprule", r"Rate (\%) & Qwen & Mistral & Haiku & Maj. \\", r"\midrule"]
PIDq = M["pooled_id"]
JS = [None, M.get("mistral_judge_pooled", {}), M.get("haiku_judge_pooled", {}), M.get("majority_judge_pooled", {})]
def cellj(J, c, metric):
    d = PIDq.get(f"{c}|{metric}") if J is None else J.get(f"id|{c}|{metric}")
    return f"{100 * d['mean']:.0f}" if d else "--"
ROWS = [("plain", "NEW_post|rebut", r"Plain: rebut \NEW{}-post"), ("plain", "OLD|rebut", r"\quad rebut \OLD{}"), ("plain", "STALE_PRE|rebut", r"\quad rebut \STR{}"),
        ("plain", "NEVER|rebut", r"\quad rebut \NEV{}"), ("premise", "NEW_post|rebut", r"PC: rebut \NEW{}-post"), ("premise", "OLD|rebut", r"\quad rebut \OLD{}"),
        ("premise", "NEVER|rebut", r"\quad rebut \NEV{}"), ("rag_fresh", "NEW_post|rebut", r"RAG-fresh: rebut \NEW{}-post"), ("rag_stale", "NEW_post|rebut", r"RAG-stale: rebut \NEW{}-post"),
        ("policy", "NEW_post|rebut", r"Policy: rebut \NEW{}-post"), ("policy", "NEW_post|cannot_verify", r"\quad defer \NEW{}-post")]
for c, metric, lab in ROWS:
    L.append(lab + " & " + " & ".join(cellj(J, c, metric) for J in JS) + r" \\")
L += [r"\bottomrule\end{tabular}",
      r"\caption{Top: agreement between labellers (Cohen's $\kappa$, three classes; refusals merged into \emph{cannot verify}). Bottom: headline rates for the models with an identified cutoff, recomputed under each judge and the 3-judge majority (Maj.). PC = Premise-check.}",
      r"\label{tab:judge}\end{table}"]
open(os.path.join(TD, "judge.tex"), "w").write("\n".join(L) + "\n")

# Table: template sweep (Plain, all 3 templates on the same items)
SW = M["template_sweep"]
swm = [m for m in MODEL_ORDER if SW.get(f"{m}|NEW", {}).get("T1", {}).get("n")]
# 2026-11-20 layout: no \resizebox; shorter spanners (rates are rebuttals, see caption), right-aligned numbers
L = [r"\begin{table}[t]\centering\small\setlength\tabcolsep{3.6pt}", r"\begin{tabular}{@{}l ccc c ccc@{}}", r"\toprule",
     r" & \multicolumn{4}{c}{\NEW{}-post (true)} & \multicolumn{3}{c}{\NEV{} (false)} \\ \cmidrule(lr){2-5}\cmidrule(l){6-8}",
     r"Model & T1 & T2 & T3 & incons. & T1 & T2 & T3 \\", r"\midrule"]
for m in swm:
    a, b = SW[f"{m}|NEW"], SW[f"{m}|FALSE"]
    L.append(f"{PRETTY[m]} & {pc(a['T1'])} & {pc(a['T2'])} & {pc(a['T3'])} & {pc(SW[f'{m}|NEW|inconsistent'])} & {pc(b['T1'])} & {pc(b['T2'])} & {pc(b['T3'])} \\\\")
L += [r"\bottomrule\end{tabular}", r"\caption{Template sweep under \textsc{Plain}: rebuttal rates (\%%) on %d \NEW{}-post and %d \NEV{} items per model. Incons.: share of new truths rebutted under some templates but not others.}" % (M["n_items"]["NEW_post"], M["n_items"]["NEVER"]), r"\label{tab:sweep}\end{table}"]
pad_cols(L, range(1, 8)); open(os.path.join(TD, "sweep.tex"), "w").write("\n".join(L) + "\n")

# numbers.tex
N = {}
def put(k, v): N[k] = v
put("NItems", str(sum(M["n_items"].values())))
put("NNewPost", str(M["n_items"]["NEW_post"])); put("NNever", str(M["n_items"]["NEVER"])); put("NStalePre", str(M["n_items"]["STALE_PRE"]))
put("NOld", str(M["n_items"]["OLD"])); put("NStalePost", str(M["n_items"]["STALE_POST"])); put("NNewNear", str(M["n_items"]["NEW_near"]))
ngen = 0
for f in glob.glob(os.path.join(R, "results", "gen", "*.jsonl")):
    ngen += sum(1 for _ in open(f))
put("NGen", f"{ngen:,}".replace(",", "{,}"))
put("NFull", str(len(M["full_models"])))
for c in CONDS:
    tag = {"plain": "Plain", "premise": "Prem", "date": "Date", "rag_fresh": "Ragf", "rag_stale": "Rags", "policy": "Pol", "policy_nodate": "Polnd"}[c]
    for key, name in (("NEW_post|rebut", "FRR"), ("NEVER|rebut", "Catch"), ("OLD|rebut", "FRROld"), ("NEW_post|cannot_verify", "CVNew"),
                      ("STALE_POST|rebut", "STPRebut"), ("STALE_POST|accept", "STPAcc"), ("FALSE|rebut", "CatchAll"), ("NEW_near|rebut", "FRRNear"),
                      ("STALE_PRE|rebut", "CatchPre"), ("NEW_post|accept", "AccNew"), ("NEVER|nonaccept", "NonaccNever")):
        put(f"{name}{tag}", f"{100 * P[f'{c}|{key}']['mean']:.0f}")
        if name in ("FRR", "Catch"):
            put(f"{name}{tag}CI", f"[{100 * P[f'{c}|{key}']['ci'][0]:.0f}, {100 * P[f'{c}|{key}']['ci'][1]:.0f}]")
V = M["verifier"]
vm = [V[f"{m}|plain"] for m in MODEL_ORDER if f"{m}|plain" in V and m != "qwen2.5-0.5b"]
for k, nm in (("auroc_never_vs_new", "AUCNevNew"), ("auroc_never_vs_old", "AUCNevOld"), ("auroc_stalepre_vs_new", "AUCPreNew")):
    vals = [v[k] for v in vm if v[k] is not None]
    put(nm + "Min", f"{min(vals):.2f}"); put(nm + "Max", f"{max(vals):.2f}")
pn = [v["mean_pno"] for v in vm]
put("PNoNewMin", f"{min(p['NEW_post'] for p in pn):.2f}"); put("PNoNewMax", f"{max(p['NEW_post'] for p in pn):.2f}")
allv = [V[f"{m}|plain"]["mean_pno"] for m in MODEL_ORDER if f"{m}|plain" in V]
put("NVerModels", str(len(allv))); put("NNewGtPre", str(sum(p["NEW_post"] > p["STALE_PRE"] for p in allv)))
put("PNoPreMin", f"{min(p['STALE_PRE'] for p in pn):.2f}"); put("PNoPreMax", f"{max(p['STALE_PRE'] for p in pn):.2f}")
put("PNoOldMin", f"{min(p['OLD'] for p in pn):.2f}"); put("PNoOldMax", f"{max(p['OLD'] for p in pn):.2f}")
put("KappaQM", f2(A["kappa_qwen_mistral"])); put("KappaQR", f2(A["kappa_qwen_rules_all"])); put("NSubset", str(A["n_subset"]))
put("NTests", str(len(TESTS))); put("MDEModel", f"{100 * M['power']['mde_per_model']:.0f}"); put("MDEPooled", f"{100 * M['power']['mde_pooled']:.0f}")
for m in models:
    cu = CUT.get(m)
    if cu:
        tag = "".join(ch for ch in PRETTY[m].replace(".", "p").replace("-", "") if ch.isalnum())
        put(f"Cut{tag}", cu["cutoff"]); put(f"CutLo{tag}", cu["ci"][0]); put(f"CutHi{tag}", cu["ci"][1])
# a-priori identified-cutoff subset macros (suffix Id)
for c in CONDS:
    tag = {"plain": "Plain", "premise": "Prem", "date": "Date", "rag_fresh": "Ragf", "rag_stale": "Rags", "policy": "Pol", "policy_nodate": "Polnd"}[c]
    for key, name in (("NEW_post|rebut", "FRR"), ("NEVER|rebut", "Catch"), ("OLD|rebut", "FRROld"), ("NEW_post|cannot_verify", "CVNew"),
                      ("STALE_PRE|rebut", "CatchPre"), ("STALE_POST|accept", "STPAcc"), ("STALE_POST|rebut", "STPRebut"), ("NEW_near|rebut", "FRRNear"),
                      ("FALSE|rebut", "CatchAll"), ("NEW_post|accept", "AccNew"), ("J_new", "Jnew"), ("J_old", "Jold")):
        d = PID[f"{c}|{key}"]
        put(f"{name}{tag}Id", f"{100 * d['mean']:.0f}"); put(f"{name}{tag}IdCI", f"[{100 * d['ci'][0]:.0f}, {100 * d['ci'][1]:.0f}]")
    put(f"Jnew{tag}", f"{100 * M['discrimination'][f'{c}|new']['mean']:.0f}"); put(f"Jold{tag}", f"{100 * M['discrimination'][f'{c}|old']['mean']:.0f}")
put("NId", str(len(M["id_models"])))
for c, tag in (("rag_stale", "Rags"), ("rag_fresh", "Ragf"), ("premise", "Prem"), ("policy", "Pol"), ("plain", "Plain")):
    v = [T[f"{m}|{c}|NEW_post|rebut"]["mean"] for m in M["id_models"]]
    put(f"FRR{tag}IdMin", f"{100 * min(v):.0f}"); put(f"FRR{tag}IdMax", f"{100 * max(v):.0f}")
    v = [T[f"{m}|{c}|NEVER|rebut"]["mean"] for m in M["id_models"]]
    put(f"Catch{tag}IdMin", f"{100 * min(v):.0f}"); put(f"Catch{tag}IdMax", f"{100 * max(v):.0f}")
sg = lambda v: ("+" if v > 0 else "$-$") + f"{abs(100 * v):.0f}"
for nm, sfx in (("all", ""), ("id", "Id")):
    for c in CONDS[1:]:
        tag = {"premise": "Prem", "date": "Date", "rag_fresh": "Ragf", "rag_stale": "Rags", "policy": "Pol", "policy_nodate": "Polnd"}[c]
        for met, mn in (("FRR_new", "DFRR"), ("FRR_old", "DOld"), ("catch_never", "DCatch"), ("catch_false", "DCatchAll"), ("accept_false", "DAccFalse")):
            d = M["deltas"][f"{nm}|{c}|{met}"]
            put(f"{mn}{tag}{sfx}", sg(d["mean"])); put(f"{mn}{tag}{sfx}CI", f"[{100 * d['ci'][0]:.0f}, {100 * d['ci'][1]:.0f}]")
MC = M["memory_conflict"]
for nm, sfx in (("all", ""), ("id", "Id")):
    put(f"MCYes{sfx}", f"{100 * MC[f'{nm}|believes_old=True']['mean']:.0f}"); put(f"MCNo{sfx}", f"{100 * MC[f'{nm}|believes_old=False']['mean']:.0f}")
    put(f"MCYesN{sfx}", str(MC[f'{nm}|believes_old=True']['n'])); put(f"MCNoN{sfx}", str(MC[f'{nm}|believes_old=False']['n']))
    put(f"MCDiff{sfx}", sg(MC[f"{nm}|diff"]["mean"])); put(f"MCDiff{sfx}CI", f"[{100 * MC[f'{nm}|diff']['ci'][0]:.0f}, {100 * MC[f'{nm}|diff']['ci'][1]:.0f}]")
RG = M.get("regressions", {})
if "error" not in RG:
    for nm, sfx in (("all", ""), ("id", "Id")):
        a = RG[f"{nm}|rebut ~ believes_old + logsl + C(model) + C(rel)"]
        put(f"RegPop{sfx}", f"{a['logsl']['coef']:.2f}"); put(f"RegPopSE{sfx}", f"{a['logsl']['se']:.2f}")
        pv = a["logsl"]["p"]; ex = int(np.floor(np.log10(pv))); put(f"RegPopP{sfx}", f"{pv / 10 ** ex:.0f}\\times10^{{{ex}}}")
        put(f"RegOld{sfx}", f"{a['believes_old']['coef']:.2f}"); put(f"RegOldSE{sfx}", f"{a['believes_old']['se']:.2f}"); put(f"RegOldP{sfx}", f"{a['believes_old']['p']:.2f}")
        put(f"RegN{sfx}", str(a["n"]))
for k in ("low", "mid", "high"):
    d = B["pop|plain|NEW_all"][k]; put(f"Pop{k.capitalize()}", f"{100 * d['mean']:.0f}")
for g in ("NEW_post", "NEW_near"):
    pass
nsig = sum(1 for t in TESTS if t["p_holm"] < 0.05); put("NSig", str(nsig))
RF = M["refusal_rate"]; put("RefQOneFive", f"{100 * RF.get('qwen2.5-1.5b|plain', 0):.0f}")
SW = M["template_sweep"]
sw_models = sorted({k.split("|")[0] for k, v in SW.items() if k.count("|") == 1 and v.get("T1", {}).get("n")})
put("NSweepModels", str(len(sw_models)))
inc = [SW[f"{m}|NEW|inconsistent"]["mean"] for m in sw_models if SW.get(f"{m}|NEW|inconsistent", {}).get("mean") is not None]
if inc: put("SweepIncMin", f"{100 * min(inc):.0f}"); put("SweepIncMax", f"{100 * max(inc):.0f}")
SJ = M.get("second_judge_rates", {})
for jn in ("qwen", "mistral"):
    for c in ("plain", "premise", "rag_fresh", "rag_stale", "policy"):
        tag = {"plain": "Plain", "premise": "Prem", "rag_fresh": "Ragf", "rag_stale": "Rags", "policy": "Pol"}[c]
        for g, gn in (("NEW_post", "New"), ("NEVER", "Nev"), ("OLD", "Old")):
            d = SJ.get(f"{jn}|{c}|{g}|rebut")
            if d: put(f"SJ{jn.capitalize()}{gn}{tag}", f"{100 * d['mean']:.0f}")
PMn = M.get("predecessor_mention", {})
for k, nm in (("plain|rebut", "PredPlain"), ("rag_stale|rebut", "PredRags"), ("policy|cannot_verify", "PredPolCV")):
    if k in PMn: put(nm, f"{100 * PMn[k]['mean']:.0f}"); put(nm + "N", str(PMn[k]["n"]))
MJ = M.get("mistral_judge_pooled", {})
for c in CONDS:
    tag = {"plain": "Plain", "premise": "Prem", "date": "Date", "rag_fresh": "Ragf", "rag_stale": "Rags", "policy": "Pol", "policy_nodate": "Polnd"}[c]
    for key, nm in (("NEW_post|rebut", "MJFRR"), ("OLD|rebut", "MJOld"), ("NEVER|rebut", "MJCatch"), ("STALE_PRE|rebut", "MJCatchPre"), ("NEW_post|cannot_verify", "MJCV")):
        for sub_, sfx in (("id", "Id"), ("all", "")):
            d = MJ.get(f"{sub_}|{c}|{key}")
            put(f"{nm}{tag}{sfx}", f"{100 * d['mean']:.0f}" if d else "\\pending{MJ}")
    d = MJ.get(f"id|{c}|NEW_post|rebut")
for jn, pre in (("haiku", "HJ"), ("majority", "VJ")):
    JJ = M.get(f"{jn}_judge_pooled", {})
    for c in CONDS:
        tag = {"plain": "Plain", "premise": "Prem", "date": "Date", "rag_fresh": "Ragf", "rag_stale": "Rags", "policy": "Pol", "policy_nodate": "Polnd"}[c]
        for key, nm in (("NEW_post|rebut", "FRR"), ("OLD|rebut", "Old"), ("NEVER|rebut", "Catch"), ("STALE_PRE|rebut", "CatchPre"), ("NEW_post|cannot_verify", "CV")):
            for sub_, sfx in (("id", "Id"), ("all", "")):
                d = JJ.get(f"{sub_}|{c}|{key}")
                put(f"{pre}{nm}{tag}{sfx}", f"{100 * d['mean']:.0f}" if d else "\\pending{%s}" % jn)
A_ = M["agreement"]
for k, nm in (("kappa_qwen_haiku", "KappaQH"), ("kappa_mistral_haiku", "KappaMH"), ("kappa_haiku_rules", "KappaHR"), ("kappa_qwen_majority", "KappaQV")):
    put(nm, f2(A_.get(k)))
put("NHaiku", f"{A_.get('n_haiku', 0):,}".replace(",", "{,}"))
cov = [v.get("coverage", 0) for v in MJ.values()]
put("MJCoverage", f"{100 * min(cov):.0f}" if cov else "0")
spreads = []
for m in sw_models:
    for g in ("NEW",):
        t = SW.get(f"{m}|{g}", {})
        vals = [t[x]["mean"] for x in ("T1", "T2", "T3") if t.get(x, {}).get("mean") is not None]
        if len(vals) == 3: spreads.append(max(vals) - min(vals))
put("SweepSpreadMax", f"{100 * max(spreads):.0f}" if spreads else "\\pending{sweep}")
uf = os.path.join(R, "results", "labels", "claude-haiku-5-5", "usage.log")
put("HaikuCost", f"{sum(json.loads(l)['cost_usd'] for l in open(uf)):.2f}" if os.path.exists(uf) else "0")
RT = M.get("retest", {})
if RT:
    put("RetestLabMin", f"{100 * min(v['same_label'] for v in RT.values()):.0f}"); put("RetestLabMax", f"{100 * max(v['same_label'] for v in RT.values()):.0f}")
    put("RetestTextMin", f"{100 * min(v['same_text'] for v in RT.values()):.0f}"); put("RetestTextMax", f"{100 * max(v['same_text'] for v in RT.values()):.0f}")
incid = [SW[f"{m}|NEW|inconsistent"]["mean"] for m in M["id_models"] if SW.get(f"{m}|NEW|inconsistent", {}).get("mean") is not None]
if incid: put("SweepIncIdMin", f"{100 * min(incid):.0f}"); put("SweepIncIdMax", f"{100 * max(incid):.0f}")
with open(os.path.join(R, "numbers.tex"), "w") as f:
    f.write("% AUTO-GENERATED by code/make_tables.py from results/analysis/*.json -- do not edit\n")
    for k, v in N.items():
        kk = "".join(ch for ch in k if ch.isalpha())
        if kk != k: kk = k.replace("0", "Zero").replace("1", "One").replace("2", "Two").replace("3", "Three").replace("4", "Four").replace("5", "Five").replace("6", "Six").replace("7", "Seven").replace("8", "Eight").replace("9", "Nine")
        f.write(f"\\newcommand{{\\{kk}}}{{{v}}}\n")
json.dump(N, open(os.path.join(R, "results", "analysis", "numbers.json"), "w"), indent=1)
print("tables ok", len(N), "macros")
