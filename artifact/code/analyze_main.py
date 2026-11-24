"""Main analysis: rates with bootstrap CIs, trade-off points, paired McNemar tests with Holm correction,
breakdowns (relation, popularity, time since change, template, size), verifier curves, judge agreement.
Writes results/analysis/main.json (+ csv tables)."""
import json, os, glob, collections, math, sys
import numpy as np
from scipy.stats import binomtest, norm
sys.path.insert(0, os.path.dirname(__file__))
from rules import label as rule_label
R = os.path.join(os.path.dirname(__file__), "..")
A = os.path.join(R, "results", "analysis"); os.makedirs(A, exist_ok=True)
rng = np.random.default_rng(0)
NB = 2000
POST = "2025-01-01"   # all estimated cutoffs (and their 95% CI upper ends) precede this date

EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))   # round-3: audited items only, as in analyze_v2/v3
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl"))) if i["id"] not in EXCL}
def group(i):
    if i["cond"] == "NEW":
        return "NEW_post" if i["t_change"] >= POST else "NEW_near"
    return i["cond"]
FALSE_KNOWABLE = ("STALE_PRE", "NEVER")

RAW = {}
SWEEP_LABELS = {}
def load_labels(judge):
    """3-way labels; the judge's 4th option 'refuse' (declines to engage, no position on P) is merged into
    'cannot_verify' (non-committal) for all rates; raw refusal rates are reported separately.
    Main-grid labels only: template-sweep files are kept apart (SWEEP_LABELS[judge]) because greedy decoding on MPS
    is not bit-identical across batch compositions, so a sweep re-run of the assigned template can differ."""
    L = {}; SWEEP_LABELS[judge] = {}
    for f in glob.glob(os.path.join(R, "results", "labels", judge, "*.jsonl")):
        if f.endswith(("_anc.jsonl", "_long.jsonl")): continue   # round-1 controls/checks are analysed in analyze_v2.py
        if f.endswith("_sweep.jsonl"):
            for l in open(f):
                r = json.loads(l)
                if r["id"] not in items: continue
                SWEEP_LABELS[judge][(r["model"], r["id"], r["icond"], r["template"])] = "cannot_verify" if r["label"] == "refuse" else r["label"]
            continue
        for l in open(f):
            r = json.loads(l); k = (r["model"], r["id"], r["icond"], r["template"])
            if r["id"] not in items: continue   # round 3: audited main-grid items only (triples and exclusions elsewhere)
            RAW[(judge,) + k] = r["label"]
            L[k] = "cannot_verify" if r["label"] == "refuse" else r["label"]
    return L
def rule3(resp):
    l = rule_label(resp); return "cannot_verify" if l == "refuse" else l
gens = {}; sweep_gens = {}
for f in glob.glob(os.path.join(R, "results", "gen", "*.jsonl")):
    if f.endswith(("_anc.jsonl", "_long.jsonl")): continue
    tgt = sweep_gens if f.endswith("_sweep.jsonl") else gens
    for l in open(f):
        r = json.loads(l)
        if r["id"] in items: tgt[(r["model"], r["id"], r["icond"], r["template"])] = r["response"]
LQ = load_labels("qwen2.5-7b")
LM = load_labels("mistral-7b")
LH = load_labels("claude-haiku-5-5")   # third judge (API), see code/judge_api.py
models = sorted({k[0] for k in LQ})
conds = ["plain", "premise", "date", "rag_fresh", "rag_stale", "policy", "policy_nodate"]

def main_rows(model, icond, lab=LQ):
    """item_id -> label for the assigned template."""
    out = {}
    for iid, it in items.items():
        k = (model, iid, icond, it["template"])
        if k in lab: out[iid] = lab[k]
    return out

def boot_ci(x):
    x = np.asarray(x, float)
    if len(x) == 0: return [None, None]
    bs = x[rng.integers(0, len(x), (NB, len(x)))].mean(1)
    return [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]

def rate(vals):
    return dict(mean=float(np.mean(vals)) if len(vals) else None, ci=boot_ci(vals), n=len(vals))

res = dict(models=models, post_date=POST, n_items=collections.Counter(group(i) for i in items.values()))
# 1. rates table
table = {}
for m in models:
    for c in conds:
        lab = main_rows(m, c)
        if not lab: continue
        for g in ["NEW_post", "NEW_near", "OLD", "STALE_POST", "STALE_PRE", "NEVER"]:
            ids = [i for i in lab if group(items[i]) == g]
            for L in ("rebut", "accept", "cannot_verify"):
                table[f"{m}|{c}|{g}|{L}"] = rate([lab[i] == L for i in ids])
        fk = [i for i in lab if group(items[i]) in FALSE_KNOWABLE]
        table[f"{m}|{c}|FALSE|rebut"] = rate([lab[i] == "rebut" for i in fk])
        table[f"{m}|{c}|FALSE|nonaccept"] = rate([lab[i] != "accept" for i in fk])
res["table"] = table

# 2. pooled across models (item-cluster bootstrap: resample items, average over models)
def pooled(c, g, L, ms=None, neg=False):
    ms = ms or [m for m in models if main_rows(m, c)]
    ids = [i for i in items if (group(items[i]) in g if isinstance(g, tuple) else group(items[i]) == g)]
    M = np.array([[float((main_rows(m, c).get(i) == L) != neg) if i in main_rows(m, c) else np.nan for m in ms] for i in ids])
    point = float(np.nanmean(M))
    bs = [np.nanmean(M[rng.integers(0, len(ids), len(ids))]) for _ in range(1000)]
    return dict(mean=point, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], n_items=len(ids), n_models=len(ms))
_cache = {}
def mr(m, c):
    if (m, c) not in _cache: _cache[(m, c)] = main_rows_orig(m, c)
    return _cache[(m, c)]
main_rows_orig = main_rows
main_rows = lambda m, c, lab=LQ: mr(m, c) if lab is LQ else main_rows_orig(m, c, lab)
full_models = [m for m in models if all(mr(m, c) for c in conds)]
res["full_models"] = full_models
P = {}
for c in conds:
    P[f"{c}|NEW_post|rebut"] = pooled(c, "NEW_post", "rebut", full_models)
    P[f"{c}|OLD|rebut"] = pooled(c, "OLD", "rebut", full_models)
    P[f"{c}|FALSE|rebut"] = pooled(c, FALSE_KNOWABLE, "rebut", full_models)
    P[f"{c}|FALSE|nonaccept"] = pooled(c, FALSE_KNOWABLE, "accept", full_models, neg=True)
    P[f"{c}|STALE_POST|rebut"] = pooled(c, "STALE_POST", "rebut", full_models)
    P[f"{c}|NEW_post|cannot_verify"] = pooled(c, "NEW_post", "cannot_verify", full_models)
    P[f"{c}|NEVER|rebut"] = pooled(c, "NEVER", "rebut", full_models)
    P[f"{c}|NEVER|nonaccept"] = pooled(c, "NEVER", "accept", full_models, neg=True)
    P[f"{c}|NEW_near|rebut"] = pooled(c, "NEW_near", "rebut", full_models)
    P[f"{c}|NEW_post|accept"] = pooled(c, "NEW_post", "accept", full_models)
    P[f"{c}|STALE_POST|accept"] = pooled(c, "STALE_POST", "accept", full_models)
    P[f"{c}|STALE_PRE|rebut"] = pooled(c, "STALE_PRE", "rebut", full_models)
res["pooled"] = P

# discrimination (Youden-style J): rebut(NEVER) - rebut(NEW_post) and rebut(NEVER) - rebut(OLD), item-cluster bootstrap per group
def jstat(c, gt, ms):
    def mat(g):
        ids = [i for i in items if group(items[i]) == g]
        return np.array([[float(mr(m, c).get(i) == "rebut") if i in mr(m, c) else np.nan for m in ms] for i in ids])
    A_, B_ = mat("NEVER"), mat(gt)
    pt = float(np.nanmean(A_) - np.nanmean(B_)); bs = []
    for _ in range(1000):
        bs.append(np.nanmean(A_[rng.integers(0, len(A_), len(A_))]) - np.nanmean(B_[rng.integers(0, len(B_), len(B_))]))
    return dict(mean=pt, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
J = {}
for c in conds:
    J[f"{c}|new"] = jstat(c, "NEW_post", full_models); J[f"{c}|old"] = jstat(c, "OLD", full_models)
    for m in models:
        if mr(m, c):
            J[f"{m}|{c}|new"] = jstat(c, "NEW_post", [m]); J[f"{m}|{c}|old"] = jstat(c, "OLD", [m])
res["discrimination"] = J

# 3. paired McNemar tests vs plain, Holm-corrected over all (model, intervention, metric)
tests = []
for m in models:
    base = mr(m, "plain")
    for c in conds[1:]:
        lab = mr(m, c)
        if not lab: continue
        for metric, g, L in (("FRR_new", ("NEW_post",), "rebut"), ("FRR_old", ("OLD",), "rebut"), ("catch_never", ("NEVER",), "rebut"),
                             ("catch_false", FALSE_KNOWABLE, "rebut"), ("rebut_stalepost", ("STALE_POST",), "rebut"), ("cv_new", ("NEW_post",), "cannot_verify")):
            ids = [i for i in lab if i in base and group(items[i]) in g]
            b = sum(1 for i in ids if base[i] == L and lab[i] != L)   # plain yes, intervention no
            cc = sum(1 for i in ids if base[i] != L and lab[i] == L)
            p = binomtest(b, b + cc, 0.5).pvalue if b + cc > 0 else 1.0
            d = (sum(lab[i] == L for i in ids) - sum(base[i] == L for i in ids)) / max(len(ids), 1)
            tests.append(dict(model=m, cond=c, metric=metric, n=len(ids), b=b, c=cc, delta=d, p=p))
order = sorted(range(len(tests)), key=lambda k: tests[k]["p"]); K = len(tests); run = 0
for r, k in enumerate(order):
    run = max(run, min(1.0, (K - r) * tests[k]["p"])); tests[k]["p_holm"] = run
res["tests"] = tests

# 4. breakdowns under plain + premise + policy (pooled over full models, NEW_post rebut and NEVER rebut)
def rate_by(keyf, g, c, L="rebut", ms=None):
    ms = ms or full_models; out = collections.defaultdict(list)
    for m in ms:
        lab = mr(m, c)
        for i, l in lab.items():
            if group(items[i]) in g: out[keyf(items[i])].append(l == L)
    return {k: dict(mean=float(np.mean(v)), ci=boot_ci(v), n=len(v)) for k, v in sorted(out.items())}
REL = {"P6": "head of gov.", "P35": "head of state", "P169": "CEO", "P286": "head coach", "P488": "chairperson"}
br = {}
for c in ("plain", "premise", "policy"):
    br[f"rel|{c}|NEW"] = rate_by(lambda i: REL[i["rel"]], ("NEW_post",), c)
    br[f"rel|{c}|FALSE"] = rate_by(lambda i: REL[i["rel"]], FALSE_KNOWABLE, c)
    br[f"tpl|{c}|NEW"] = rate_by(lambda i: i["template"], ("NEW_post",), c)
    br[f"tpl|{c}|FALSE"] = rate_by(lambda i: i["template"], FALSE_KNOWABLE, c)
# popularity tertiles by entity sitelinks among NEW items
sl = sorted(i["y_sl"] for i in items.values() if i["cond"] == "NEW")
t1, t2 = np.percentile(sl, [33.3, 66.7])
popk = lambda i: "low" if i["y_sl"] <= t1 else ("mid" if i["y_sl"] <= t2 else "high")
for c in ("plain", "premise", "policy"):
    br[f"pop|{c}|NEW"] = rate_by(popk, ("NEW_post",), c)
    br[f"pop|{c}|NEW_all"] = rate_by(popk, ("NEW_post", "NEW_near"), c)
res["pop_cuts"] = [float(t1), float(t2)]
# time since change: half-year bins over all NEW items, per model
def halfyear(i): d = i["t_change"]; return f"{d[:4]}H{1 if d[5:7] <= '06' else 2}"
for m in models:
    for c in ("plain", "premise", "policy"):
        if mr(m, c): br[f"time|{m}|{c}"] = rate_by(halfyear, ("NEW_post", "NEW_near"), c, ms=[m])
for c in ("plain", "premise", "policy"):
    br[f"time|pooled|{c}"] = rate_by(halfyear, ("NEW_post", "NEW_near"), c)
    br[f"time|pooled|{c}|cv"] = rate_by(halfyear, ("NEW_post", "NEW_near"), c, L="cannot_verify")
res["breakdowns"] = br

# 5. template sweep (plain, all three templates on the same items) for sweep models
sweep = {}
for f in glob.glob(os.path.join(R, "results", "gen", "*_sweep.jsonl")):
    m = os.path.basename(f).replace("_sweep.jsonl", "")
    per = collections.defaultdict(dict)
    for k, l in SWEEP_LABELS["claude-haiku-5-5"].items():   # primary judge (round-1 revision)
        if k[0] == m and k[2] == "plain": per[k[1]][k[3]] = l
    # round-3: the false columns use NEVER only (false under every template; STALE_PRE is historically true under T1/T3)
    for g, gs in (("NEW", ("NEW_post",)), ("FALSE", ("NEVER",)), ("OLD", ("OLD",))):
        ids = [i for i in per if i in items and len(per[i]) == 3 and group(items[i]) in gs]
        sweep[f"{m}|{g}"] = {t: rate([per[i][t] == "rebut" for i in ids]) for t in ("T1", "T2", "T3")}
        # flip rate: item-level disagreement across templates
        sweep[f"{m}|{g}|inconsistent"] = rate([len({per[i][t] == "rebut" for t in ("T1", "T2", "T3")}) > 1 for i in ids])
# test-retest: the sweep re-generates each item's assigned template in Plain (different batch composition)
rt = {}
for m in models:
    ks = [k for k in SWEEP_LABELS["claude-haiku-5-5"] if k[0] == m and k[2] == "plain" and k[1] in items and k[3] == items[k[1]]["template"] and k in LH]
    if ks:
        rt[m] = dict(n=len(ks), same_text=float(np.mean([sweep_gens.get(k) == gens.get(k) for k in ks])),
                     same_label=float(np.mean([SWEEP_LABELS["claude-haiku-5-5"][k] == LH[k] for k in ks])),
                     kappa=None)
res["retest"] = rt
res["template_sweep"] = sweep

# 6. verifier curves + AUROC
def auroc(pos, neg):
    pos, neg = np.asarray(pos), np.asarray(neg)
    if len(pos) == 0 or len(neg) == 0: return None
    gt = (pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()
    return float(gt)
ver = {}
for f in glob.glob(os.path.join(R, "results", "verify", "*.jsonl")):
    m = os.path.basename(f)[:-6]
    V = collections.defaultdict(dict)
    for l in open(f):
        r = json.loads(l)
        if r["id"] in items: V[r["var"]][r["id"]] = r["p_no"]
    for var, d in V.items():
        g = lambda gs: [d[i] for i in d if group(items[i]) in gs]
        newp, oldp, fal, nev, stp = g(("NEW_post",)), g(("OLD",)), g(FALSE_KNOWABLE), g(("NEVER",)), g(("STALE_PRE",))
        taus = np.linspace(0, 1, 101)
        curve = [[float(np.mean(np.array(newp) > t)), float(np.mean(np.array(fal) > t)), float(np.mean(np.array(oldp) > t))] for t in taus]
        ver[f"{m}|{var}"] = dict(auroc_false_vs_new=auroc(fal, newp), auroc_false_vs_old=auroc(fal, oldp),
                                 auroc_never_vs_new=auroc(nev, newp), auroc_never_vs_old=auroc(nev, oldp),
                                 auroc_stalepre_vs_new=auroc(stp, newp),
                                 mean_pno=dict(NEW_post=float(np.mean(newp)), OLD=float(np.mean(oldp)), NEVER=float(np.mean(nev)), STALE_PRE=float(np.mean(stp))),
                                 curve=curve,
                                 curve_never=[[float(np.mean(np.array(newp) > t)), float(np.mean(np.array(nev) > t)), float(np.mean(np.array(oldp) > t))] for t in taus])
res["verifier"] = ver

# 7. judge agreement
def kappa(a, b):
    labs = ["accept", "rebut", "cannot_verify"]; n = len(a)
    if n == 0: return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labs)
    return (po - pe) / (1 - pe) if pe < 1 else None
keys = [k for k in LM if k in LQ]
qa = [LQ[k] for k in keys]; ma = [LM[k] for k in keys]; ra = [rule3(gens[k]) for k in keys]
allk = [k for k in LQ if k in gens]
agree = dict(n_subset=len(keys), kappa_qwen_mistral=kappa(qa, ma), acc_qwen_mistral=float(np.mean([x == y for x, y in zip(qa, ma)])) if keys else None,
             kappa_qwen_rules_subset=kappa(qa, ra), kappa_mistral_rules_subset=kappa(ma, ra),
             n_all=len(allk), kappa_qwen_rules_all=kappa([LQ[k] for k in allk], [rule3(gens[k]) for k in allk]),
             majority_agree_with_qwen=float(np.mean([(q == mm) or (q == r) for q, mm, r in zip(qa, ma, ra)])) if keys else None)
# self-judging check: agreement on Qwen-family outputs vs others
for fam, pred in (("qwen_outputs", lambda m: m.startswith("qwen")), ("other_outputs", lambda m: not m.startswith("qwen"))):
    ks = [k for k in keys if pred(k[0])]
    agree[f"kappa_qwen_mistral_{fam}"] = kappa([LQ[k] for k in ks], [LM[k] for k in ks]); agree[f"n_{fam}"] = len(ks)
# confusion matrix
conf = collections.Counter((LQ[k], LM[k]) for k in keys)
agree["confusion_qwen_rows_mistral_cols"] = {f"{a}|{b}": v for (a, b), v in conf.items()}
# robustness: headline pooled metrics under the second judge (subset) and under the rules
res["agreement"] = agree
# refusal rates (raw 4th judge option) per model x condition
refr = {}
for m in models:
    for c in conds:
        ks = [("qwen2.5-7b", m, iid, c, it["template"]) for iid, it in items.items() if ("qwen2.5-7b", m, iid, c, it["template"]) in RAW]
        if ks: refr[f"{m}|{c}"] = float(np.mean([RAW[k] == "refuse" for k in ks]))
res["refusal_rate"] = refr

# 8. headline robustness under alternative labelers (all generations, rules)
alt = {}
for c in conds:
    for name, lf in (("rules", lambda k: rule3(gens[k])),):
        vals_new, vals_false = [], []
        for m in full_models:
            for iid, it in items.items():
                k = (m, iid, c, it["template"])
                if k not in gens: continue
                if group(it) == "NEW_post": vals_new.append(lf(k) == "rebut")
                if group(it) in FALSE_KNOWABLE: vals_false.append(lf(k) == "rebut")
        alt[f"{name}|{c}"] = dict(FRR_new=float(np.mean(vals_new)) if vals_new else None, catch=float(np.mean(vals_false)) if vals_false else None)
res["alt_labeler"] = alt

# 9. power: minimum detectable difference for paired McNemar at n NEW_post items (alpha .05, power .8), given discordance 20%
n_new = sum(1 for i in items.values() if group(i) == "NEW_post")
def mde(n, pdisc=0.2, alpha=0.05, power=0.8):
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return (za * math.sqrt(pdisc) + zb * math.sqrt(pdisc)) / math.sqrt(n)
res["power"] = dict(n_new_post=n_new, mde_per_model=mde(n_new), mde_pooled=mde(n_new * len(full_models)))
# 10. a-priori subset: models whose effective cutoff the date probe identifies (permutation p<.05 and a downward step).
#     This criterion uses only the probe, never the outcome labels.
CUT = json.load(open(os.path.join(A, "cutoffs.json")))
id_models = [m for m in full_models if CUT.get(m, {}).get("perm_p", 1) < 0.05 and CUT[m]["p_before"] > CUT[m]["p_after"]]
res["id_models"] = id_models
PID = {}
for c in conds:
    for key, g, L, neg in (("NEW_post|rebut", "NEW_post", "rebut", False), ("OLD|rebut", "OLD", "rebut", False),
                           ("NEVER|rebut", "NEVER", "rebut", False), ("STALE_PRE|rebut", "STALE_PRE", "rebut", False),
                           ("FALSE|rebut", FALSE_KNOWABLE, "rebut", False), ("NEW_post|cannot_verify", "NEW_post", "cannot_verify", False),
                           ("NEW_post|accept", "NEW_post", "accept", False), ("STALE_POST|rebut", "STALE_POST", "rebut", False),
                           ("STALE_POST|accept", "STALE_POST", "accept", False), ("NEW_near|rebut", "NEW_near", "rebut", False),
                           ("NEVER|nonaccept", "NEVER", "accept", True)):
        PID[f"{c}|{key}"] = pooled(c, g, L, id_models, neg=neg)
    PID[f"{c}|J_new"] = jstat(c, "NEW_post", id_models); PID[f"{c}|J_old"] = jstat(c, "OLD", id_models)
res["pooled_id"] = PID

# 11. paired deltas vs Plain (item-cluster bootstrap over items; same items, same models), all-model and id subsets
def pdelta(c, g, L, ms, neg=False):
    ids = [i for i in items if (group(items[i]) in g if isinstance(g, tuple) else group(items[i]) == g)]
    def M_(cc): return np.array([[float((mr(m, cc).get(i) == L) != neg) if i in mr(m, cc) else np.nan for m in ms] for i in ids])
    D = M_(c) - M_("plain"); pt = float(np.nanmean(D))
    bs = [np.nanmean(D[rng.integers(0, len(ids), len(ids))]) for _ in range(2000)]
    return dict(mean=pt, ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
DL = {}
for nm, ms in (("all", full_models), ("id", id_models)):
    for c in conds[1:]:
        DL[f"{nm}|{c}|FRR_new"] = pdelta(c, "NEW_post", "rebut", ms)
        DL[f"{nm}|{c}|FRR_old"] = pdelta(c, "OLD", "rebut", ms)
        DL[f"{nm}|{c}|catch_never"] = pdelta(c, "NEVER", "rebut", ms)
        DL[f"{nm}|{c}|catch_false"] = pdelta(c, FALSE_KNOWABLE, "rebut", ms)
        DL[f"{nm}|{c}|accept_false"] = pdelta(c, FALSE_KNOWABLE, "accept", ms)
res["deltas"] = DL

# 12. memory conflict: does a model rebut a NEW-post premise more when its own verifier still endorses the predecessor?
#     Each NEW-post item is paired (same entity, relation) with exactly one STALE-POST item about the predecessor.
pair = {}
sp = {(i["y"], i["rel"]): iid for iid, i in items.items() if i["cond"] == "STALE_POST"}
for iid, i in items.items():
    if group(i) == "NEW_post" and (i["y"], i["rel"]) in sp: pair[iid] = sp[(i["y"], i["rel"])]
VER = {}
for f in glob.glob(os.path.join(R, "results", "verify", "*.jsonl")):
    m = os.path.basename(f)[:-6]
    for l in open(f):
        r = json.loads(l)
        if r["var"] == "plain": VER[(m, r["id"])] = r["p_no"]
conf_rows = []
for m in full_models:
    lab = mr(m, "plain")
    for n_id, s_id in pair.items():
        if n_id in lab and (m, s_id) in VER and (m, n_id) in VER:
            conf_rows.append(dict(model=m, id=n_id, believes_old=VER[(m, s_id)] < 0.5, pno_new=VER[(m, n_id)],
                                  rebut=lab[n_id] == "rebut", rel=items[n_id]["rel"], logsl=math.log1p(items[n_id]["y_sl"])))
MC = {}
for nm, ms in (("all", full_models), ("id", id_models)):
    rows = [r for r in conf_rows if r["model"] in ms]
    for b in (True, False):
        v = [r["rebut"] for r in rows if r["believes_old"] == b]
        MC[f"{nm}|believes_old={b}"] = rate(v)
    # item-cluster bootstrap of the difference
    byi = collections.defaultdict(list)
    for r in rows: byi[r["id"]].append(r)
    ids_ = list(byi)
    def diff(sel):
        rr = [r for i in sel for r in byi[i]]
        a = [r["rebut"] for r in rr if r["believes_old"]]; b_ = [r["rebut"] for r in rr if not r["believes_old"]]
        return (np.mean(a) - np.mean(b_)) if a and b_ else np.nan
    bs = [diff([ids_[k] for k in rng.integers(0, len(ids_), len(ids_))]) for _ in range(2000)]
    MC[f"{nm}|diff"] = dict(mean=float(diff(ids_)), ci=[float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))])
for m in full_models:
    rows = [r for r in conf_rows if r["model"] == m]
    for b in (True, False):
        MC[f"{m}|believes_old={b}"] = rate([r["rebut"] for r in rows if r["believes_old"] == b])
res["memory_conflict"] = MC

# 13. logistic regressions (Plain, NEW-post rebut): popularity and predecessor belief, with model and relation fixed effects,
#     cluster-robust SEs by item.
try:
    import statsmodels.formula.api as smf, pandas as pd
    df = pd.DataFrame(conf_rows); df["rebut"] = df["rebut"].astype(int); df["believes_old"] = df["believes_old"].astype(int)
    df["item"] = pd.factorize(df["id"])[0]
    REG = {}
    for nm, ms in (("all", full_models), ("id", id_models)):
        d = df[df.model.isin(ms)]
        for form in ("rebut ~ logsl + C(model) + C(rel)", "rebut ~ believes_old + C(model) + C(rel)",
                     "rebut ~ believes_old + logsl + C(model) + C(rel)"):
            fit = smf.logit(form, d).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d["item"]})
            REG[f"{nm}|{form}"] = {k: dict(coef=float(fit.params[k]), se=float(fit.bse[k]), p=float(fit.pvalues[k]))
                                   for k in ("logsl", "believes_old") if k in fit.params}
            REG[f"{nm}|{form}"]["n"] = int(len(d))
    res["regressions"] = REG
except Exception as e:
    res["regressions"] = dict(error=str(e))

# 14. second-judge robustness: pooled rates on the subset under each judge (same keys)
SJ = {}
if keys:
    for jn, Lab in (("qwen", LQ), ("mistral", LM)):
        for c in conds:
            for g, gs in (("NEW_post", ("NEW_post",)), ("OLD", ("OLD",)), ("NEVER", ("NEVER",)), ("FALSE", FALSE_KNOWABLE)):
                for nm, ms in (("", full_models), ("id|", id_models)):
                    for L in ("rebut", "cannot_verify"):
                        v = [Lab[k] == L for k in keys if k[2] == c and k[0] in ms and group(items[k[1]]) in gs]
                        if v: SJ[f"{nm}{jn}|{c}|{g}|{L}"] = rate(v)
res["second_judge_rates"] = SJ

# 15. full replication under the second judge (when it has labelled the main grid): pooled id-subset rates + J + deltas
def pooled_lab(c, g, L, ms, lab):
    ids = [i for i in items if (group(items[i]) in g if isinstance(g, tuple) else group(items[i]) == g)]
    rows = {m: main_rows_orig(m, c, lab) for m in ms}
    Mx = np.array([[float(rows[m].get(i) == L) if i in rows[m] else np.nan for m in ms] for i in ids])
    if np.all(np.isnan(Mx)): return None
    bs = [np.nanmean(Mx[rng.integers(0, len(ids), len(ids))]) for _ in range(1000)]
    return dict(mean=float(np.nanmean(Mx)), ci=[float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))],
                coverage=float(np.mean(~np.isnan(Mx))))
FULLM = {}
for c in conds:
    for key, g, L in (("NEW_post|rebut", "NEW_post", "rebut"), ("OLD|rebut", "OLD", "rebut"), ("NEVER|rebut", "NEVER", "rebut"),
                      ("STALE_PRE|rebut", "STALE_PRE", "rebut"), ("NEW_post|cannot_verify", "NEW_post", "cannot_verify")):
        for nm, ms in (("id", id_models), ("all", full_models)):
            d = pooled_lab(c, g, L, ms, LM)
            if d: FULLM[f"{nm}|{c}|{key}"] = d
res["mistral_judge_pooled"] = FULLM

# 15b. third judge (Claude Haiku 5.5) and the 3-judge majority label
def majority(k):
    v = [d[k] for d in (LQ, LM, LH) if k in d]
    if len(v) < 3: return None
    c = collections.Counter(v).most_common()
    return c[0][0] if c[0][1] >= 2 else "cannot_verify"   # 3-way split -> non-committal
LMAJ = {k: majority(k) for k in LQ if majority(k) is not None}
for nmj, LAB_ in (("haiku", LH), ("majority", LMAJ)):
    D = {}
    for c in conds:
        for key, g, L in (("NEW_post|rebut", "NEW_post", "rebut"), ("OLD|rebut", "OLD", "rebut"), ("NEVER|rebut", "NEVER", "rebut"),
                          ("STALE_PRE|rebut", "STALE_PRE", "rebut"), ("NEW_post|cannot_verify", "NEW_post", "cannot_verify")):
            for nm, ms in (("id", id_models), ("all", full_models)):
                d = pooled_lab(c, g, L, ms, LAB_)
                if d: D[f"{nm}|{c}|{key}"] = d
    res[f"{nmj}_judge_pooled"] = D
kh = [k for k in LH if k in LQ]
res["agreement"].update(n_haiku=len(kh),
    kappa_qwen_haiku=kappa([LQ[k] for k in kh], [LH[k] for k in kh]) if kh else None,
    kappa_mistral_haiku=kappa([LM[k] for k in kh if k in LM], [LH[k] for k in kh if k in LM]) if kh else None,
    n_mistral_haiku=sum(1 for k in kh if k in LM),
    kappa_haiku_rules=kappa([LH[k] for k in kh], [rule3(gens[k]) for k in kh]) if kh else None,
    n_majority=len(LMAJ),
    kappa_qwen_majority=kappa([LQ[k] for k in LMAJ], [LMAJ[k] for k in LMAJ]) if LMAJ else None,
    confusion_qwen_rows_haiku_cols={f"{a}|{b}": v for (a, b), v in collections.Counter((LQ[k], LH[k]) for k in kh).items()})


# 16. error analysis: does a rebuttal of a NEW-post premise name the immediate predecessor (surname match)?
PM = {}
for c in ("plain", "premise", "rag_stale", "policy"):
    for lab_ in ("rebut", "cannot_verify"):
        hits = []
        for m in id_models:
            for iid, l_ in mr(m, c).items():
                it = items[iid]
                if group(it) == "NEW_post" and l_ == lab_:
                    hits.append(it["old_l"].split()[-1].lower() in gens[(m, iid, c, it["template"])].lower())
        if hits: PM[f"{c}|{lab_}"] = dict(mean=float(np.mean(hits)), n=len(hits))
res["predecessor_mention"] = PM



json.dump(res, open(os.path.join(A, "main.json"), "w"), indent=1, default=lambda o: dict(o) if isinstance(o, collections.Counter) else str(o))
print("models", models, "full", full_models)
for c in conds:
    print(c, {k.split("|", 1)[1]: round(v["mean"], 3) for k, v in P.items() if k.startswith(c + "|")})
print(json.dumps(agree, indent=0)[:800])
