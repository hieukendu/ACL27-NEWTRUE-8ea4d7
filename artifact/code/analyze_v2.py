"""Revised main analysis (round 1) -> results/analysis/v2.json

Design changes after round-1 review (see reviews/round1/meta.md):
- Primary labels: Claude Haiku 5.5 (not an evaluated model; best agreement with Claude Sonnet 5.5 silver labels).
  Robustness: Qwen2.5-7B judge, Mistral-7B judge, 3-judge majority.
- Items: audit exclusions (data/exclusions.json) removed everywhere.
- Controls: NEW_post (true, became true >= 2025-01-01, after the release of every pooled model);
            OLD (true, unchanged since <= 2021/2022); ANC (entity-matched false: a holder of the same role at the same
            entity who left before 2016; same template); STR_early (false: holder replaced before 2021-01-01);
            NEVER (implausible false, sanity check only); STALE_POST (secondary).
- Model sets: ALL = 7 models with every condition (no selection); KNOW = 4 models whose date probe shows knowledge of
  office holders (secondary). Pooled estimates use a two-level bootstrap (models and items resampled).
"""
import json, os, glob, math, collections
import numpy as np
R = os.path.join(os.path.dirname(__file__), "..")
A = os.path.join(R, "results", "analysis")
rng = np.random.default_rng(2)
NB = 2000
M0 = json.load(open(os.path.join(A, "main.json")))
ALLM = M0["full_models"]; KNOW = M0["id_models"]
EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl"))) if i["id"] not in EXCL}
anc = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items_ancient.jsonl"))) if i["pair"] not in EXCL}
ALL = {**items, **anc}
def group(it):
    c = it["cond"]
    if c == "NEW": return "NEW_post" if it["t_change"] >= "2025-01-01" else "NEW_near"
    if c == "STALE_PRE": return "STR_early" if it["t_change"] < "2021-01-01" else "STR_late"
    if c == "STALE_ANCIENT": return "ANC"
    return c
G = collections.defaultdict(list)
for i, it in ALL.items(): G[group(it)].append(i)

def load(judge, keep):
    L = {}
    for f in glob.glob(os.path.join(R, "results", "labels", judge, "*.jsonl")):
        if not keep(os.path.basename(f)): continue
        for l in open(f):
            r = json.loads(l)
            L[(r["model"], r["id"], r["icond"], r["template"])] = "cannot_verify" if r["label"] == "refuse" else r["label"]
    return L
main_or_anc = lambda b: not any(s in b for s in ("_sweep", "_long"))
J = {"haiku": load("claude-haiku-5-5", main_or_anc), "qwen": load("qwen2.5-7b", main_or_anc), "mistral": load("mistral-7b", main_or_anc)}
def majority(k):
    v = [J[j][k] for j in ("haiku", "qwen", "mistral") if k in J[j]]
    if len(v) < 3: return None
    c = collections.Counter(v).most_common()
    return c[0][0] if c[0][1] >= 2 else "cannot_verify"
J["majority"] = {k: m for k in J["haiku"] if (m := majority(k)) is not None}
PRIMARY = "haiku"
CONDS = ["plain", "premise", "date", "rag_fresh", "rag_stale_u", "policy", "policy_nodate", "cutoff_date", "rag_mixed", "rag_stale"]

def mat(lab, cond, ids, ms, L="rebut"):
    return np.array([[float(lab[k] == L) if (k := (m, i, cond, ALL[i]["template"])) in lab else np.nan for m in ms] for i in ids])
def two_level(fn, ms, n_items_groups):
    """fn(model_idx, item_idx_per_group) -> value; resample models and, independently, items within each group."""
    vals = []
    for _ in range(NB):
        mi = rng.integers(0, len(ms), len(ms))
        ii = [rng.integers(0, n, n) for n in n_items_groups]
        v = fn(mi, ii)
        if not np.isnan(v): vals.append(v)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [None, None]
def pooled_rate(lab, cond, g, ms, L="rebut"):
    X = mat(lab, cond, G[g], ms, L)
    if X.size == 0 or np.all(np.isnan(X)): return None
    ci = two_level(lambda mi, ii: np.nanmean(X[ii[0]][:, mi]), ms, [X.shape[0]])
    return dict(mean=float(np.nanmean(X)), ci=ci, n_items=X.shape[0], n_models=len(ms))
def pooled_diff(lab, cond, ga, gb, ms, L="rebut", cond_b=None):
    """rate(ga, cond) - rate(gb, cond_b or cond); two-level bootstrap (shared model resample)."""
    Xa = mat(lab, cond, G[ga], ms, L); Xb = mat(lab, cond_b or cond, G[gb], ms, L)
    if Xa.size == 0 or Xb.size == 0 or np.all(np.isnan(Xa)) or np.all(np.isnan(Xb)): return None
    f = lambda mi, ii: np.nanmean(Xa[ii[0]][:, mi]) - np.nanmean(Xb[ii[1]][:, mi])
    pt = float(np.nanmean(Xa) - np.nanmean(Xb))
    return dict(mean=pt, ci=two_level(f, ms, [Xa.shape[0], Xb.shape[0]]))
def paired_anc(lab, cond, ms):
    """Within-entity: rebut(ANC false) - rebut(paired NEW_post true), same model/condition/template; two-level bootstrap over
    models and entities. Also per-model exact McNemar on discordant pairs."""
    ids = [a for a in G["ANC"] if anc[a]["pair"] in items]
    Xa = mat(lab, cond, ids, ms); Xn = mat(lab, cond, [anc[a]["pair"] for a in ids], ms)
    D = Xa - Xn
    if np.all(np.isnan(D)): return None
    out = dict(mean=float(np.nanmean(D)), rebut_new=float(np.nanmean(Xn)), rebut_anc=float(np.nanmean(Xa)), n_pairs=len(ids),
               ci=two_level(lambda mi, ii: np.nanmean(D[ii[0]][:, mi]), ms, [len(ids)]))
    from scipy.stats import binomtest
    pm = {}
    for j, m in enumerate(ms):
        b = int(np.nansum((Xa[:, j] == 1) & (Xn[:, j] == 0))); c = int(np.nansum((Xa[:, j] == 0) & (Xn[:, j] == 1)))
        pm[m] = dict(anc_only=b, new_only=c, p=float(binomtest(b, b + c, .5).pvalue) if b + c else 1.0,
                     rebut_new=float(np.nanmean(Xn[:, j])), rebut_anc=float(np.nanmean(Xa[:, j])))
    out["per_model"] = pm
    return out

res = dict(models_all=ALLM, models_know=KNOW, primary_judge=PRIMARY, n_excluded=len(EXCL),
           n_items={g: len(v) for g, v in G.items()})
P = {}; D = {}; PA = {}
for jn, lab in J.items():
    for sn, ms in (("all", ALLM), ("know", KNOW)):
        for c in CONDS:
            for g in ("NEW_post", "NEW_near", "OLD", "ANC", "STR_early", "STR_late", "NEVER", "STALE_POST"):
                for L in ("rebut", "cannot_verify", "accept"):
                    d = pooled_rate(lab, c, g, ms, L)
                    if d: P[f"{jn}|{sn}|{c}|{g}|{L}"] = d
            for ga, gb, nm in (("NEW_post", "OLD", "new_minus_old"), ("STR_early", "NEW_post", "Jpre"), ("NEVER", "NEW_post", "Jnev")):
                d = pooled_diff(lab, c, ga, gb, ms)
                if d: D[f"{jn}|{sn}|{c}|{nm}"] = d
            pa = paired_anc(lab, c, ms)
            if pa: PA[f"{jn}|{sn}|{c}"] = pa
            if c != "plain":   # intervention deltas vs Plain on the same items (paired by item and model)
                for g in ("NEW_post", "OLD", "ANC", "STR_early", "NEVER"):
                    X1 = mat(lab, c, G[g], ms); X0 = mat(lab, "plain", G[g], ms); DD = X1 - X0
                    if not np.all(np.isnan(DD)):
                        D[f"{jn}|{sn}|{c}|delta|{g}"] = dict(mean=float(np.nanmean(DD)),
                                                             ci=two_level(lambda mi, ii, DD=DD: np.nanmean(DD[ii[0]][:, mi]), ms, [DD.shape[0]]))
res["rates"] = P; res["diffs"] = D; res["paired_anc"] = PA

# per-model table (primary judge): rebut rates by group for key conditions
PM = {}
for m in M0["models"]:
    for c in CONDS:
        for g in ("NEW_post", "OLD", "ANC", "STR_early", "NEVER"):
            X = mat(J[PRIMARY], c, G[g], [m])
            if X.size and not np.all(np.isnan(X)): PM[f"{m}|{c}|{g}"] = dict(mean=float(np.nanmean(X)), n=int(np.sum(~np.isnan(X))))
        X = mat(J[PRIMARY], c, G["NEW_post"], [m], "cannot_verify")
        if X.size and not np.all(np.isnan(X)): PM[f"{m}|{c}|NEW_post|defer"] = dict(mean=float(np.nanmean(X)))
res["per_model"] = PM

# regressions (Plain, primary judge): condition effects with entity & person popularity, model and relation FE, item clusters
try:
    import pandas as pd, statsmodels.formula.api as smf
    REG = {}
    for sn, ms in (("all", ALLM), ("know", KNOW)):
        rows = []
        # round-3: the withdrawn T1/T3 ANC items are no longer in the regression; template fixed effects added
        for i in G["NEW_post"] + G["OLD"] + G["STR_early"]:
            it = ALL[i]
            for m in ms:
                k = (m, i, "plain", it["template"])
                if k in J[PRIMARY]:
                    rows.append(dict(rebut=int(J[PRIMARY][k] == "rebut"), g=group(it), logsl=math.log1p(it["y_sl"]),
                                     logpx=math.log1p(it.get("x_sl", 0) or 0), model=m, rel=it["rel"], tmpl=it["template"], item=it.get("pair", i)))
        df = pd.DataFrame(rows); df["cl"] = pd.factorize(df["item"])[0]
        for nm, form in (("cond+pop", "rebut ~ C(g, Treatment('NEW_post')) + logsl + C(model) + C(rel) + C(tmpl)"),):
            fit = smf.logit(form, df).fit(disp=0, cov_type="cluster", cov_kwds={"groups": df["cl"]})
            REG[f"{sn}|{nm}"] = {k.replace("C(g, Treatment('NEW_post'))", "g"): dict(coef=float(fit.params[k]), se=float(fit.bse[k]), p=float(fit.pvalues[k]))
                                for k in fit.params.index if k.startswith("C(g") or k in ("logsl", "logpx")}
            REG[f"{sn}|{nm}"]["n"] = int(len(df))
        # unfamiliarity: among NEW_post (true), does person popularity predict rebuttal? (entity popularity controlled)
        dn = df[df.g == "NEW_post"].copy()
        if "logpx" in dn and dn["logpx"].std() > 0:
            ci_ = lambda f, k: [float(x) for x in f.conf_int().loc[k]]
            fit = smf.logit("rebut ~ logpx + logsl + C(model) + C(rel) + C(tmpl)", dn).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dn["cl"]})
            REG[f"{sn}|person_fame_NEW"] = {k: dict(coef=float(fit.params[k]), se=float(fit.bse[k]), p=float(fit.pvalues[k]), ci=ci_(fit, k)) for k in ("logpx", "logsl")}
            REG[f"{sn}|person_fame_NEW"]["n"] = int(len(dn))
            # round-3: entity popularity among NEW_post items only (the coefficient the text cites), same controls
            fit = smf.logit("rebut ~ logsl + C(model) + C(rel) + C(tmpl)", dn).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dn["cl"]})
            REG[f"{sn}|pop_NEW"] = dict(logsl=dict(coef=float(fit.params["logsl"]), se=float(fit.bse["logsl"]), p=float(fit.pvalues["logsl"]), ci=ci_(fit, "logsl")), n=int(len(dn)))
    res["regressions"] = REG
except Exception as e:
    res["regressions"] = dict(error=repr(e))
res["median_sitelinks"] = {g: float(np.median([ALL[i]["y_sl"] for i in G[g]])) for g in G}
res["median_person_sitelinks"] = {g: float(np.median([ALL[i].get("x_sl", 0) or 0 for i in G[g]])) for g in G}

# judge validation against silver labels (Claude Sonnet 5.5)
sf = os.path.join(R, "results", "labels", "silver-claude-sonnet-5-5", "silver.jsonl")
if os.path.exists(sf):
    S = {}
    for l in open(sf):
        r = json.loads(l)
        if r["key"][1] in ALL: S[tuple(r["key"])] = "cannot_verify" if r["label"] == "refuse" else r["label"]
    labs = ["accept", "rebut", "cannot_verify"]
    def kappa(a, b):
        n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; pe = sum(a.count(l) / n * b.count(l) / n for l in labs); return (po - pe) / (1 - pe)
    SV = dict(n=len(S))
    for jn, lab in J.items():
        ks = [k for k in S if k in lab]; a = [lab[k] for k in ks]; b = [S[k] for k in ks]
        tp = sum(x == "rebut" and y == "rebut" for x, y in zip(a, b))
        SV[jn] = dict(n=len(ks), acc=float(np.mean([x == y for x, y in zip(a, b)])), kappa=kappa(a, b),
                      rebut_precision=tp / max(1, sum(x == "rebut" for x in a)), rebut_recall=tp / max(1, sum(y == "rebut" for y in b)),
                      rebut_rate=float(np.mean([x == "rebut" for x in a])), silver_rebut_rate=float(np.mean([y == "rebut" for y in b])))
    res["silver"] = SV

# long-generation check (256 tokens) under qwen and mistral judges (haiku added if labelled)
LG = {}
for jn, jdir in (("qwen", "qwen2.5-7b"), ("mistral", "mistral-7b"), ("haiku", "claude-haiku-5-5")):
    labL = load(jdir, lambda b: "_long" in b); lab = J[jn]
    for g in ("NEW_post", "OLD", "STR_early"):
        pr = [(lab[k], labL[k]) for k in labL if k in lab and k[1] in ALL and group(ALL[k[1]]) == g]
        if pr: LG[f"{jn}|{g}"] = dict(n=len(pr), rebut_48=float(np.mean([a == "rebut" for a, _ in pr])), rebut_256=float(np.mean([b == "rebut" for _, b in pr])),
                                      same=float(np.mean([a == b for a, b in pr])))
res["long_generation"] = LG
# belief probe on the audited groups: mean P(No) (Plain verifier) per model for NEW_post, OLD, STR_early, ANC n/a (not probed)
VB = {}
for f in glob.glob(os.path.join(R, "results", "verify", "*.jsonl")):
    m = os.path.basename(f)[:-6]; d = collections.defaultdict(list)
    for l in open(f):
        r = json.loads(l)
        if r["var"] == "plain" and r["id"] in items: d[group(items[r["id"]])].append(r["p_no"])
    VB[m] = {g: float(np.mean(v)) for g, v in d.items() if v}
res["belief"] = VB
res["belief_new_gt_stre"] = sum(1 for v in VB.values() if v.get("NEW_post", 0) > v.get("STR_early", 1))
# round-3: count over the 7 pooled models only, and also report how often long-true OLD premises get a higher P(No) than STR_early
res["belief_pooled"] = dict(n=sum(1 for m in ALLM if m in VB), new_gt_stre=sum(1 for m in ALLM if m in VB and VB[m].get("NEW_post", 0) > VB[m].get("STR_early", 1)),
                            old_gt_stre=sum(1 for m in ALLM if m in VB and VB[m].get("OLD", 0) > VB[m].get("STR_early", 1)))
# acceptance of false premises (ANC + STR_early) per condition, all and know
AF = {}
for jn in ("haiku",):
    for sn, ms in (("all", ALLM), ("know", KNOW)):
        for c in CONDS:
            X = np.vstack([mat(J[jn], c, G[g], ms, "accept") for g in ("ANC", "STR_early")])
            if not np.all(np.isnan(X)): AF[f"{jn}|{sn}|{c}"] = float(np.nanmean(X))
res["accept_false"] = AF
# predecessor-belief test (primary judge, audited items): NEW_post items paired with the STALE_POST item about the same
# entity's predecessor; "believes predecessor" = the model's own yes/no P(No) < 0.5 on that STALE_POST item
VERP = {}
for f in glob.glob(os.path.join(R, "results", "verify", "*.jsonl")):
    m = os.path.basename(f)[:-6]
    for l in open(f):
        r = json.loads(l)
        if r["var"] == "plain": VERP[(m, r["id"])] = r["p_no"]
spm = {(it["y"], it["rel"]): i for i, it in items.items() if it["cond"] == "STALE_POST"}
rowsb = []
for i in G["NEW_post"]:
    it = items[i]; sp = spm.get((it["y"], it["rel"]))
    if not sp: continue
    for m in ALLM:
        k = (m, i, "plain", it["template"])
        if k in J[PRIMARY] and (m, sp) in VERP:
            rowsb.append(dict(rebut=int(J[PRIMARY][k] == "rebut"), believes=int(VERP[(m, sp)] < 0.5), logsl=math.log1p(it["y_sl"]), model=m, rel=it["rel"], item=i))
if rowsb:
    import pandas as pd, statsmodels.formula.api as smf
    dfb = pd.DataFrame(rowsb); dfb["cl"] = pd.factorize(dfb["item"])[0]
    fit = smf.logit("rebut ~ believes + logsl + C(model)", dfb).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dfb["cl"]})
    res["predecessor_belief"] = dict(n=len(dfb), rebut_believes=float(dfb[dfb.believes == 1].rebut.mean()), rebut_not=float(dfb[dfb.believes == 0].rebut.mean()),
                                     n_believes=int(dfb.believes.sum()), coef=float(fit.params["believes"]), p=float(fit.pvalues["believes"]))
json.dump(res, open(os.path.join(A, "v2.json"), "w"), indent=1)
print("n_items", res["n_items"]); print("silver", {k: round(v["acc"], 3) for k, v in res.get("silver", {}).items() if isinstance(v, dict)})
