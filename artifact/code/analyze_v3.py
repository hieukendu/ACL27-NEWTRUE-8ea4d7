"""Round-2 analysis (+ round-3 additions in analyze_v3_r3.py, executed at the end) -> results/analysis/v3.json

Main test (all T2, "as the current r"): for each audited NEW-post entity a triple
  N = newly-true holder (true), A = alive former holder who left before 2016 (false, familiar), S = another entity's 2025+
  holder (false, unfamiliar, familiarity matched to N).
Gaps: J_fam = rebut(A) - rebut(N), J_unf = rebut(S) - rebut(N). Pooled over 7 models with a two-level bootstrap (models and
entities); model-level tests on the 7 per-model gaps (one-sample t and Wilcoxon); condition changes in J tested by bootstrap
of the paired difference.
Also: main-grid groups (NEW_post, NEW_near, OLD, STR_early, STR_late, STALE_POST) with the audited items; every judge, the 3-judge
majority and Claude Sonnet 5.5 silver labels (held-out sample on the triples); error-analysis counts."""
import json, os, glob, collections, math, re
import numpy as np
from scipy import stats
R = os.path.join(os.path.dirname(__file__), "..")
A = os.path.join(R, "results", "analysis")
rng = np.random.default_rng(4)
NB = 2000
M0 = json.load(open(os.path.join(A, "main.json")))
ALLM = M0["full_models"]; KNOW = M0["id_models"]
EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl"))) if i["id"] not in EXCL}
v3 = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items_v3.jsonl"))) if i["pair"] not in EXCL}
ALL = {**items, **v3}
def group(it):
    c = it["cond"]
    if c == "NEW": return "NEW_post" if it["t_change"] >= "2025-01-01" else "NEW_near"
    if c == "STALE_PRE": return "STR_early" if it["t_change"] < "2021-01-01" else "STR_late"
    return c
G = collections.defaultdict(list)
for i, it in ALL.items(): G[group(it)].append(i)
TRI = collections.defaultdict(dict)
for i, it in v3.items(): TRI[it["pair"]][it["cond"]] = i
TRI = {p: d for p, d in TRI.items() if len(d) == 3}
PAIRS = sorted(TRI)

def load(judge):
    L = {}
    for f in glob.glob(os.path.join(R, "results", "labels", judge, "*.jsonl")):
        b = os.path.basename(f)
        if any(s in b for s in ("_sweep", "_long", "_anc", "_pairs_t2")): continue
        for l in open(f):
            r = json.loads(l)
            L[(r["model"], r["id"], r["icond"], r["template"])] = "cannot_verify" if r["label"] == "refuse" else r["label"]
    return L
J = {"haiku": load("claude-haiku-5-5"), "qwen": load("qwen2.5-7b"), "mistral": load("mistral-7b"),
     "codex": load("openai-gpt-5.3-codex")}   # cross-family judge (OpenAI), held-out set
def maj(k):
    v = [J[j][k] for j in ("haiku", "qwen", "mistral") if k in J[j]]
    if len(v) < 3: return None
    c = collections.Counter(v).most_common(); return c[0][0] if c[0][1] >= 2 else "cannot_verify"
J["majority"] = {k: m for k in J["haiku"] if (m := maj(k))}
SIL = {}
for f in glob.glob(os.path.join(R, "results", "labels", "silver-claude-sonnet-5-5", "silver*.jsonl")):
    for l in open(f):
        r = json.loads(l); SIL[tuple(r["key"])] = "cannot_verify" if r["label"] == "refuse" else r["label"]
J["silver"] = SIL
PRIMARY = "haiku"
CONDS = ["plain", "premise", "premise_fq", "premise_ragf", "date", "cutoff_date", "rag_fresh", "rag_mixed_u", "rag_stale_u", "policy", "policy_nodate"]

def mat_ids(lab, cond, ids, ms, L="rebut"):
    return np.array([[float(lab[k] == L) if (k := (m, i, cond, ALL[i]["template"])) in lab else np.nan for m in ms] for i in ids])
def tri_mats(lab, cond, ms, L="rebut"):
    return {c: mat_ids(lab, cond, [TRI[p][c] for p in PAIRS], ms, L) for c in ("P3_NEW", "P3_ANC", "P3_SWAP")}
def boot(fn, n_models, n_items):
    vals = []
    for _ in range(NB):
        mi = rng.integers(0, n_models, n_models); ii = rng.integers(0, n_items, n_items)
        v = fn(mi, ii)
        if not np.isnan(v): vals.append(v)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [None, None]
def model_level(D):
    """D: entity x model matrix of paired differences -> per-model means, t-test and Wilcoxon across models."""
    pm = np.nanmean(D, axis=0); pm = pm[~np.isnan(pm)]
    if len(pm) < 3: return dict(per_model=pm.tolist())
    t = stats.ttest_1samp(pm, 0.0)
    try: w = stats.wilcoxon(pm).pvalue
    except ValueError: w = 1.0
    return dict(per_model=[float(x) for x in pm], t_p=float(t.pvalue), wilcoxon_p=float(w), n_pos=int((pm > 0).sum()), n_neg=int((pm < 0).sum()))

res = dict(models_all=ALLM, models_know=KNOW, n_triples=len(PAIRS), n_items={g: len(v) for g, v in G.items()}, primary=PRIMARY)
TR = {}
for jn, lab in J.items():
    for sn, ms in (("all", ALLM), ("know", KNOW)):
        for c in CONDS:
            Mx = tri_mats(lab, c, ms)
            if all(np.all(np.isnan(x)) for x in Mx.values()): continue
            out = {}
            for k, x in Mx.items():
                out[f"rate_{k}"] = float(np.nanmean(x)) if not np.all(np.isnan(x)) else None
                out[f"ci_{k}"] = boot(lambda mi, ii, x=x: np.nanmean(x[ii][:, mi]), len(ms), len(PAIRS))
                out[f"defer_{k}"] = float(np.nanmean(tri_mats(lab, c, ms, "cannot_verify")[k]))
                out[f"accept_{k}"] = float(np.nanmean(tri_mats(lab, c, ms, "accept")[k]))
            for nm, a in (("Jfam", "P3_ANC"), ("Junf", "P3_SWAP")):
                D = Mx[a] - Mx["P3_NEW"]
                if np.all(np.isnan(D)): continue
                out[nm] = float(np.nanmean(D)); out[f"{nm}_ci"] = boot(lambda mi, ii, D=D: np.nanmean(D[ii][:, mi]), len(ms), len(PAIRS))
                out[f"{nm}_model"] = model_level(D)
            TR[f"{jn}|{sn}|{c}"] = out
res["triples"] = TR
PMR = {}
for m in M0["models"]:
    for c in CONDS:
        Mx = tri_mats(J[PRIMARY], c, [m])
        if all(np.all(np.isnan(x)) for x in Mx.values()): continue
        PMR[f"{m}|{c}"] = {k: (float(np.nanmean(x)) if not np.all(np.isnan(x)) else None) for k, x in Mx.items()}
res["per_model_triples"] = PMR
# scale-up models (GX10 server, CUDA): reported per model and pooled separately, never mixed into the 7-model estimates
LARGE = [m for m in ("qwen2.5-14b", "phi4", "qwen2.5-32b") if any(k[0] == m for k in J[PRIMARY])]
LG3 = {}
for m in LARGE:
    for c in CONDS:
        Mx = tri_mats(J[PRIMARY], c, [m])
        if all(np.all(np.isnan(x)) for x in Mx.values()): continue
        d = {k: float(np.nanmean(x)) for k, x in Mx.items()}
        for nm, a in (("Jfam", "P3_ANC"), ("Junf", "P3_SWAP")):
            D = (Mx[a] - Mx["P3_NEW"])[:, 0]; D = D[~np.isnan(D)]
            d[nm] = float(D.mean()); bs = [D[rng.integers(0, len(D), len(D))].mean() for _ in range(NB)]
            d[f"{nm}_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        for g in ("NEW_post", "OLD", "STR_early"):
            X = mat_ids(J[PRIMARY], c, G[g], [m]); d[g] = float(np.nanmean(X)) if not np.all(np.isnan(X)) else None
        LG3[f"{m}|{c}"] = d
if LARGE:
    for c in CONDS:
        Mx = tri_mats(J[PRIMARY], c, LARGE)
        if all(np.all(np.isnan(x)) for x in Mx.values()): continue
        out = {k: float(np.nanmean(x)) for k, x in Mx.items()}
        for nm, a in (("Jfam", "P3_ANC"), ("Junf", "P3_SWAP")):
            D = Mx[a] - Mx["P3_NEW"]; out[nm] = float(np.nanmean(D))
            out[f"{nm}_ci"] = boot(lambda mi, ii, D=D: np.nanmean(D[ii][:, mi]), len(LARGE), len(PAIRS))
        for g in ("NEW_post", "OLD"):
            out[g] = float(np.nanmean(mat_ids(J[PRIMARY], c, G[g], LARGE)))
        LG3[f"pooled|{c}"] = out
res["large"] = LG3; res["large_models"] = LARGE
# change of J between conditions (vs plain), primary judge and majority, all models
DJ = {}
for jn in ("haiku", "majority", "qwen", "mistral", "silver", "codex"):
    lab = J[jn]
    M0p = tri_mats(lab, "plain", ALLM)
    for c in CONDS[1:]:
        Mc = tri_mats(lab, c, ALLM)
        for nm, a in (("Jfam", "P3_ANC"), ("Junf", "P3_SWAP")):
            D = (Mc[a] - Mc["P3_NEW"]) - (M0p[a] - M0p["P3_NEW"])
            if np.all(np.isnan(D)): continue
            DJ[f"{jn}|{c}|{nm}"] = dict(mean=float(np.nanmean(D)), ci=boot(lambda mi, ii, D=D: np.nanmean(D[ii][:, mi]), len(ALLM), len(PAIRS)), model=model_level(D))
        Dn = Mc["P3_NEW"] - M0p["P3_NEW"]
        if not np.all(np.isnan(Dn)):
            DJ[f"{jn}|{c}|dNEW"] = dict(mean=float(np.nanmean(Dn)), ci=boot(lambda mi, ii, D=Dn: np.nanmean(D[ii][:, mi]), len(ALLM), len(PAIRS)), model=model_level(Dn))
res["dJ"] = DJ

# main-grid groups (audited): rates and NEW-post minus other groups, two-level bootstrap + model-level tests
MG = {}
for jn in ("haiku", "majority", "qwen", "mistral"):
    lab = J[jn]
    for c in CONDS:
        for g in ("NEW_post", "NEW_near", "OLD", "STR_early", "STR_late", "STALE_POST", "NEVER"):
            X = mat_ids(lab, c, G[g], ALLM)
            if X.size == 0 or np.all(np.isnan(X)): continue
            MG[f"{jn}|{c}|{g}"] = dict(mean=float(np.nanmean(X)), ci=boot(lambda mi, ii, X=X: np.nanmean(X[ii % X.shape[0]][:, mi]), len(ALLM), X.shape[0]),
                                       defer=float(np.nanmean(mat_ids(lab, c, G[g], ALLM, "cannot_verify"))),
                                       accept=float(np.nanmean(mat_ids(lab, c, G[g], ALLM, "accept"))))
        XN = mat_ids(lab, c, G["NEW_post"], ALLM); XO = mat_ids(lab, c, G["OLD"], ALLM)
        if not (np.all(np.isnan(XN)) or np.all(np.isnan(XO))):
            pmN, pmO = np.nanmean(XN, 0), np.nanmean(XO, 0); d = pmN - pmO
            MG[f"{jn}|{c}|new_minus_old_model"] = dict(per_model=[float(x) for x in d], t_p=float(stats.ttest_1samp(d, 0).pvalue),
                                                       wilcoxon_p=float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0, n_pos=int((d > 0).sum()))
for c in CONDS:   # round 3: the four knowledgeable models (for the comparison with the larger models)
    for g in ("NEW_post", "OLD", "STR_early"):
        X = mat_ids(J[PRIMARY], c, G[g], KNOW)
        if X.size and not np.all(np.isnan(X)): MG[f"{PRIMARY}|know|{c}|{g}"] = dict(mean=float(np.nanmean(X)))
res["groups"] = MG

# person familiarity in the triples
res["person_sitelinks_median"] = {c: float(np.median([v3[TRI[p][c]].get("x_sl_wd") or 0 for p in PAIRS])) for c in ("P3_NEW", "P3_ANC", "P3_SWAP")}

# error analysis of Plain rebuttals of NEW-post premises (primary judge), regex-based (approximate)
gens = {}
for f in glob.glob(os.path.join(R, "results", "gen", "*.jsonl")):
    b = os.path.basename(f)
    if any(s in b for s in ("_sweep", "_long", "_anc", "_pairs_t2", "_v3")): continue
    for l in open(f):
        r = json.loads(l); gens[(r["model"], r["id"], r["icond"], r["template"])] = r["response"]
EA = collections.Counter(); per_model_formula = {}
for k, lab_ in J[PRIMARY].items():
    if k[2] != "plain" or k[1] not in items or group(items[k[1]]) != "NEW_post" or lab_ != "rebut" or k[0] not in ALLM: continue
    it = items[k[1]]; t = gens.get(k, ""); low = t.lower()
    EA["n"] += 1
    if it.get("old_l") and it["old_l"].split()[-1].lower() in low: EA["names_predecessor"] += 1
    if re.search(r"\b(served|was|has been|had been)\b[^.]{0,60}\b(19|20)\d\d\b", t) and it["x_l"].split()[-1].lower() in low: EA["invented_tenure"] += 1
    if re.search(r"(no (information|record|knowledge|data)|not aware of|i('m| am) not familiar|not (a )?(widely )?known|unknown|could(n't| not) find|can(no|')t find|don't have (any )?(specific |up-to-date )?information|there is no (individual|person|one|record)|no (individual|person|one) (named|by the name)|does not appear to|doesn't appear to|not recognized)", low): EA["unfamiliar"] += 1
    if re.search(r"as of my (last|knowledge)|my (training|knowledge) (data|cutoff)", low): EA["cutoff_mention"] += 1
for m in ALLM:
    ks = [k for k in J[PRIMARY] if k[0] == m and k[2] == "premise" and k in gens]
    if ks: per_model_formula[m] = float(np.mean(["contains a false premise" in gens[k].lower()[:80] for k in ks]))
res["error_analysis"] = dict(EA); res["premise_formula_by_model"] = per_model_formula

# silver vs each judge on the held-out triple sample (if labelled)
HO3 = ("plain", "premise", "cutoff_date")   # round-2 held-out conditions; round 3 adds premise_ragf (reported separately)
sv = {k: v for k, v in SIL.items() if k[1] in v3 and k[2] in HO3}
labs3 = ["accept", "rebut", "cannot_verify"]
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n; pe = sum(a.count(l) / n * b.count(l) / n for l in labs3); return (po - pe) / (1 - pe)
SV = dict(n=len(sv))
for jn in ("haiku", "majority", "qwen", "mistral"):
    ks = [k for k in sv if k in J[jn]]
    if not ks: continue
    a = [J[jn][k] for k in ks]; b = [sv[k] for k in ks]
    tp = sum(x == "rebut" and y == "rebut" for x, y in zip(a, b))
    SV[jn] = dict(n=len(ks), acc=float(np.mean([x == y for x, y in zip(a, b)])), kappa=kappa(a, b),
                  rebut_precision=tp / max(1, sum(x == "rebut" for x in a)), rebut_recall=tp / max(1, sum(y == "rebut" for y in b)))
# cross-family silver: Sonnet (Anthropic) vs gpt-5.3-codex (OpenAI) on the held-out set, and each judge vs both
CX = {k: v for k, v in J["codex"].items() if k[1] in v3 and k[2] in HO3}
both = [k for k in sv if k in CX]
if both:
    a = [sv[k] for k in both]; b = [CX[k] for k in both]
    SV["sonnet_vs_codex"] = dict(n=len(both), acc=float(np.mean([x == y for x, y in zip(a, b)])), kappa=kappa(a, b))
    agree = {k: sv[k] for k in both if sv[k] == CX[k]}   # cross-family consensus labels
    SV["consensus_n"] = len(agree)
    for jn in ("haiku", "majority", "qwen", "mistral"):
        ks = [k for k in agree if k in J[jn]]
        if ks: SV[f"{jn}_vs_consensus"] = dict(n=len(ks), acc=float(np.mean([J[jn][k] == agree[k] for k in ks])),
                                               kappa=kappa([J[jn][k] for k in ks], [agree[k] for k in ks]))
# round 3: primary judge against each held-out labeller directly (no consensus filtering), for the round-2 conditions and RAG+PC
def agree(a_lab, b_lab, keys):
    ks = [k for k in keys if k in a_lab and k in b_lab]
    if not ks: return None
    a = [a_lab[k] for k in ks]; b = [b_lab[k] for k in ks]
    return dict(n=len(ks), acc=float(np.mean([x == y for x, y in zip(a, b)])), kappa=kappa(a, b))
for cs, tag in ((HO3, "ho3"), (("premise_ragf",), "ragf")):
    keys = [k for k in set(J["silver"]) | set(J["codex"]) if k[1] in v3 and k[2] in cs]
    for x, y in (("haiku", "silver"), ("haiku", "codex"), ("silver", "codex")):
        d = agree(J[x], J[y], keys)
        if d: SV[f"{tag}|{x}_vs_{y}"] = d
SV["n_keys_ho3"] = len([k for k in J["codex"] if k[1] in v3 and k[2] in HO3])
res["silver_heldout"] = SV
exec(open(os.path.join(os.path.dirname(__file__), "analyze_v3_r3.py")).read())
json.dump(res, open(os.path.join(A, "v3.json"), "w"), indent=1)
print("triples", len(PAIRS), "silver held-out", len(sv))
