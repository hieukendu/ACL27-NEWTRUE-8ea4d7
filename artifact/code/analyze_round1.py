"""Round-1 revision analyses -> results/analysis/round1.json
 1. early stale control: STALE_PRE items whose change predates 2021-01-01 (before every model's plausible training cutoff)
 2. condition effects controlled for popularity: logit(rebut) ~ condition + log sitelinks + model FE + relation FE, item-clustered
 3. T2-only comparison (template that explicitly says "the current r")
 4. entity-matched ancient-holder control (data/items_ancient.jsonl): paired NEW-post (true) vs ANC (false), same entity/template
 5. extra baselines (cutoff_date, rag_mixed) and the 256-token long-generation check
 6. date probe re-fit with per-token (length-normalised) log-probabilities
All rates use the labels of each judge separately and the 3-judge majority where available; models = identified-cutoff set."""
import json, os, glob, math, collections, sys
import numpy as np
R = os.path.join(os.path.dirname(__file__), "..")
A = os.path.join(R, "results", "analysis")
rng = np.random.default_rng(1)
M = json.load(open(os.path.join(A, "main.json")))
ID = M["id_models"]
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
anc_f = os.path.join(R, "data", "items_ancient.jsonl")
anc = {i["id"]: i for i in map(json.loads, open(anc_f))} if os.path.exists(anc_f) else {}
ALL = {**items, **anc}
def group(i):
    if i["cond"] == "NEW": return "NEW_post" if i["t_change"] >= "2025-01-01" else "NEW_near"
    if i["cond"] == "STALE_PRE": return "STALE_PRE_early" if i["t_change"] < "2021-01-01" else "STALE_PRE_late"
    return i["cond"]

def load(judge, suffix_filter):
    L = {}
    for f in glob.glob(os.path.join(R, "results", "labels", judge, "*.jsonl")):
        b = os.path.basename(f)
        if not suffix_filter(b): continue
        for l in open(f):
            r = json.loads(l)
            L[(r["model"], r["id"], r["icond"], r["template"])] = "cannot_verify" if r["label"] == "refuse" else r["label"]
    return L
is_main = lambda b: not any(s in b for s in ("_sweep", "_long", "_anc"))
JUDGES = {j: load(j, lambda b: is_main(b) or "_anc" in b) for j in ("qwen2.5-7b", "mistral-7b", "claude-haiku-5-5")}
LONG = {j: load(j, lambda b: "_long" in b) for j in ("qwen2.5-7b", "mistral-7b")}
def majority(k, Js):
    v = [J[k] for J in Js if k in J]
    if len(v) < len(Js): return None
    c = collections.Counter(v).most_common()
    return c[0][0] if c[0][1] * 2 > len(v) else "cannot_verify"
def with_majority(D):
    keys = set().union(*[set(J) for J in D.values()])
    out = dict(D); Js = list(D.values())
    out["majority"] = {k: m for k in keys if (m := majority(k, Js)) is not None}
    return out
JUDGES = with_majority(JUDGES)

def rows(lab, cond, gfilter, ms=ID, tpl=None):
    """matrix item x model of rebut indicators (nan if missing)."""
    ids = [i for i, it in ALL.items() if gfilter(it) and (tpl is None or it["template"] == tpl)]
    Mx = np.array([[float(lab[(m, i, cond, ALL[i]["template"])] == "rebut") if (m, i, cond, ALL[i]["template"]) in lab else np.nan for m in ms] for i in ids])
    return ids, Mx
def rate(lab, cond, gfilter, ms=ID, tpl=None):
    ids, Mx = rows(lab, cond, gfilter, ms, tpl)
    if len(ids) == 0 or np.all(np.isnan(Mx)): return None
    bs = [np.nanmean(Mx[rng.integers(0, len(ids), len(ids))]) for _ in range(1000)]
    return dict(mean=float(np.nanmean(Mx)), ci=[float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))], n_items=len(ids))
def diff(lab, cond, fa, fb, ms=ID, tpl=None):
    """rebut(a) - rebut(b), independent item-cluster bootstrap of each group."""
    _, A_ = rows(lab, cond, fa, ms, tpl); _, B_ = rows(lab, cond, fb, ms, tpl)
    if A_.size == 0 or B_.size == 0: return None
    pt = float(np.nanmean(A_) - np.nanmean(B_))
    bs = [np.nanmean(A_[rng.integers(0, len(A_), len(A_))]) - np.nanmean(B_[rng.integers(0, len(B_), len(B_))]) for _ in range(2000)]
    return dict(mean=pt, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
g = lambda name: (lambda it: group(it) == name)
CONDS = ["plain", "premise", "date", "rag_fresh", "rag_stale", "policy", "policy_nodate", "cutoff_date", "rag_mixed"]
out = dict(id_models=ID, n=dict(stale_pre_early=sum(1 for i in items.values() if group(i) == "STALE_PRE_early"),
                                stale_pre_late=sum(1 for i in items.values() if group(i) == "STALE_PRE_late"), ancient=len(anc)))

# 1 + 3 + 5: rates per judge
RT = {}
for jn, lab in JUDGES.items():
    for c in CONDS:
        for gn in ("NEW_post", "OLD", "NEVER", "STALE_PRE_early", "STALE_PRE_late", "STALE_POST", "STALE_ANCIENT"):
            d = rate(lab, c, g(gn))
            if d: RT[f"{jn}|{c}|{gn}"] = d
        for gn in ("NEW_post", "OLD", "STALE_PRE_early", "STALE_ANCIENT"):
            d = rate(lab, c, g(gn), tpl="T2")
            if d: RT[f"{jn}|{c}|{gn}|T2"] = d
        for gb, nm in (("STALE_PRE_early", "Jpre"), ("STALE_ANCIENT", "Janc"), ("NEVER", "Jnev")):
            d = diff(lab, c, g(gb), g("NEW_post"))
            if d: RT[f"{jn}|{c}|{nm}"] = d
        # defer rate on NEW_post
        ids = [i for i, it in ALL.items() if group(it) == "NEW_post"]
        v = [lab[(m, i, c, ALL[i]["template"])] == "cannot_verify" for m in ID for i in ids if (m, i, c, ALL[i]["template"]) in lab]
        if v: RT[f"{jn}|{c}|NEW_post|defer"] = dict(mean=float(np.mean(v)), n=len(v))
out["rates"] = RT

# 4: paired NEW-post vs ANC on the same entity (same model, condition): McNemar-style discordance + paired bootstrap
PAIR = {}
for jn, lab in JUDGES.items():
    for c in CONDS:
        pr = []
        for a in anc.values():
            n_ = ALL[a["pair"]]
            for m in ID:
                kn, ka = (m, n_["id"], c, n_["template"]), (m, a["id"], c, a["template"])
                if kn in lab and ka in lab: pr.append((a["id"], lab[kn] == "rebut", lab[ka] == "rebut"))
        if not pr: continue
        byi = collections.defaultdict(list)
        for i, x, y in pr: byi[i].append(y - x)   # rebut(false ANC) - rebut(true NEW) on the same entity
        ids_ = list(byi); pt = float(np.mean([d for i in ids_ for d in byi[i]]))
        bs = [np.mean([d for k in rng.integers(0, len(ids_), len(ids_)) for d in byi[ids_[k]]]) for _ in range(2000)]
        PAIR[f"{jn}|{c}"] = dict(rebut_new=float(np.mean([x for _, x, _ in pr])), rebut_anc=float(np.mean([y for _, _, y in pr])),
                                 J_paired=pt, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], n_pairs=len(pr), n_entities=len(ids_))
out["paired_ancient"] = PAIR

# 2: popularity-controlled condition effects (Plain), per judge
try:
    import pandas as pd, statsmodels.formula.api as smf
    REG = {}
    for jn, lab in JUDGES.items():
        rows_ = []
        for i, it in items.items():
            gn = group(it)
            if gn not in ("NEW_post", "OLD", "STALE_PRE_early", "NEVER"): continue
            for m in ID:
                k = (m, i, "plain", it["template"])
                if k in lab: rows_.append(dict(rebut=int(lab[k] == "rebut"), g=gn, logsl=math.log1p(it["y_sl"]), model=m, rel=it["rel"], item=i))
        df = pd.DataFrame(rows_); df["item_c"] = pd.factorize(df["item"])[0]
        fit = smf.logit("rebut ~ C(g, Treatment('NEW_post')) + logsl + C(model) + C(rel)", df).fit(disp=0, cov_type="cluster", cov_kwds={"groups": df["item_c"]})
        REG[jn] = {k.replace("C(g, Treatment('NEW_post'))", "g"): dict(coef=float(fit.params[k]), se=float(fit.bse[k]), p=float(fit.pvalues[k]))
                   for k in fit.params.index if "C(g" in k or k == "logsl"}
        REG[jn]["n"] = len(df)
    out["popularity_controlled"] = REG
except Exception as e:
    out["popularity_controlled"] = dict(error=str(e))
out["median_sitelinks"] = {gn: float(np.median([it["y_sl"] for it in items.values() if group(it) == gn])) for gn in ("NEW_post", "OLD", "STALE_PRE_early", "STALE_PRE_late", "NEVER")}
if anc: out["median_sitelinks"]["STALE_ANCIENT"] = float(np.median([it["y_sl"] for it in anc.values()]))

# 5b: long generation (256 tokens) vs main 48-token Plain, same item & model
LG = {}
for jn in ("qwen2.5-7b", "mistral-7b"):
    lab, labL = JUDGES[jn], LONG[jn]
    for gn in ("NEW_post", "OLD", "STALE_PRE_early"):
        pr = [(lab[k], labL[k]) for k in labL if k in lab and k[2] == "plain" and k[0] in ID and group(ALL[k[1]]) == gn]
        if pr:
            LG[f"{jn}|{gn}"] = dict(n=len(pr), rebut_48=float(np.mean([a == "rebut" for a, _ in pr])), rebut_256=float(np.mean([b == "rebut" for _, b in pr])),
                                    same_label=float(np.mean([a == b for a, b in pr])),
                                    rebut_to_other=float(np.mean([a == "rebut" and b != "rebut" for a, b in pr])),
                                    other_to_rebut=float(np.mean([a != "rebut" and b == "rebut" for a, b in pr])))
out["long_generation"] = LG

# 6: length-normalised date probe
sys.path.insert(0, os.path.dirname(__file__))
def months(d): return int(d[:4]) * 12 + int(d[5:7]) - 1
def fit_step(t, y):
    best = None
    for c in range(t.min() + 6, t.max() - 6):
        a, b = y[t < c], y[t >= c]
        if len(a) < 10 or len(b) < 10: continue
        p1, p2 = np.clip(a.mean(), 1e-3, 1 - 1e-3), np.clip(b.mean(), 1e-3, 1 - 1e-3)
        ll = (a * np.log(p1) + (1 - a) * np.log(1 - p1)).sum() + (b * np.log(p2) + (1 - b) * np.log(1 - p2)).sum()
        if best is None or ll > best[0]: best = (ll, c, float(a.mean()), float(b.mean()))
    return best
PN = {}
for f in sorted(glob.glob(os.path.join(R, "results", "probe", "*.jsonl"))):
    m = os.path.basename(f)[:-6]; P = [json.loads(l) for l in open(f)]
    t = np.array([months(p["t_change"]) for p in P])
    for nm, score in (("sum", lambda p: p["lp_new"] > p["lp_old"]), ("per_token", lambda p: p["lp_new"] / p["n_new"] > p["lp_old"] / p["n_old"])):
        y = np.array([float(score(p)) for p in P]); b = fit_step(t, y)
        ll0 = (y * np.log(np.clip(y.mean(), 1e-3, 1)) + (1 - y) * np.log(np.clip(1 - y.mean(), 1e-3, 1))).sum()
        perm = []
        for _ in range(200):
            yp = rng.permutation(y); bp = fit_step(t, yp); perm.append(bp[0] - ll0)
        PN[f"{m}|{nm}"] = dict(cutoff=f"{b[1] // 12}-{b[1] % 12 + 1:02d}", p_before=b[2], p_after=b[3], llr=float(b[0] - ll0),
                               perm_p=float((1 + sum(x >= b[0] - ll0 for x in perm)) / 201))
out["probe_normalised"] = PN
json.dump(out, open(os.path.join(A, "round1.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k in ("n", "median_sitelinks")}))
