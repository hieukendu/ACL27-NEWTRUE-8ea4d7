"""Round-3 additions to analyze_v3.py (executed at its end, in its namespace; writes into res["r3"]).
Answers the round-3 meta-review (reviews/round3/meta.md):
  1  RAG-fresh + premise-check: per-model spread, knowledgeable-model pool, what the "rebuttals" say (regex), held-out labels
  2  larger models vs the four knowledgeable small models; per-family numbers; J with CIs
  3  FreshQA wording: change in J vs Plain (t and Wilcoxon)
  4  SWAP control: within-triple person popularity, popularity-matched subset, nationality-compatible subset, OLS with person
     popularity and entity fixed effects
  5  hedged vs unhedged rebuttals (regex on the response text), J on each
  6  statistics: Wilcoxon, Holm, held-out-labeller p's, refusals split from cannot-verify
  7  main-grid groups on the present-tense template T2 only
  8  256-token Plain re-run of the triples (4 knowledgeable models)
  10 Qwen3.5-4B per model; refined invented-tenure regex; oracle deferrals
All regex-based quantities are approximate and labelled as such in the paper."""
R3 = {}
KN = KNOW
def J_of(lab, cond, ms, ids_filter=None, L="rebut"):
    """pooled rates, J_fam/J_unf with two-level CI and model-level tests, optionally on a subset of triples."""
    pairs = [p for p in PAIRS if ids_filter is None or p in ids_filter]
    Mx = {c: mat_ids(lab, cond, [TRI[p][c] for p in pairs], ms, L) for c in ("P3_NEW", "P3_ANC", "P3_SWAP")}
    out = dict(n_triples=len(pairs), n_models=len(ms))
    for k, x in Mx.items(): out[k] = float(np.nanmean(x)) if not np.all(np.isnan(x)) else None
    for nm, a in (("Jfam", "P3_ANC"), ("Junf", "P3_SWAP")):
        D = Mx[a] - Mx["P3_NEW"]
        if np.all(np.isnan(D)): continue
        out[nm] = float(np.nanmean(D)); out[f"{nm}_ci"] = boot(lambda mi, ii, D=D: np.nanmean(D[ii][:, mi]), len(ms), len(pairs))
        out[f"{nm}_model"] = model_level(D)
    return out

# ---------- raw labels (refusals kept apart) and v3 generations
def load_raw(judge, want_long=False):
    L = {}
    for f in glob.glob(os.path.join(R, "results", "labels", judge, "*_v3.jsonl")):
        if ("_long" in os.path.basename(f)) != want_long: continue
        for l in open(f):
            r = json.loads(l); L[(r["model"], r["id"], r["icond"], r["template"])] = r["label"]
    return L
RAWH = load_raw("claude-haiku-5-5")
GEN3 = {}; GENL = {}
for f in glob.glob(os.path.join(R, "results", "gen", "*_v3.jsonl")):
    tgt = GENL if "_long" in os.path.basename(f) else GEN3
    for l in open(f):
        r = json.loads(l); tgt[(r["model"], r["id"], r["icond"], r["template"])] = r["response"]

# ---------- 6 deferral split: refusals vs cannot-verify (primary judge, all models, NEW arm)
DS = {}
for c in ("plain", "cutoff_date", "rag_fresh", "premise_ragf", "date", "policy"):
    ks = [(m, TRI[p]["P3_NEW"], c, "T2") for p in PAIRS for m in ALLM]
    v = [RAWH[k] for k in ks if k in RAWH]
    if v: DS[c] = dict(refuse=float(np.mean([x == "refuse" for x in v])), cannot_verify=float(np.mean([x == "cannot_verify" for x in v])), n=len(v))
R3["defer_split"] = DS

# ---------- 5 hedged vs unhedged rebuttals
HEDGE = re.compile(r"as of (my|the) (last|latest|most recent|current)?\s*(knowledge|update|information|training|data)|as of my knowledge|"
                   r"knowledge cut-?off|cut-?off date|my (training|knowledge)( data)?|training data|last update|latest update|"
                   r"as of (early |late |mid-?)?(19|20)\d\d|as of (january|february|march|april|may|june|july|august|september|october|november|december)|"
                   r"may have changed|might have changed|could have changed|i (don't|do not) have (real-time|access to real-time|current|up-to-date)", re.I)
def hedge_lab(lab, hedged):
    """labels where 'rebut' is kept only if the response text is (un)hedged; other rebuttals become 'other'."""
    out = {}
    for k, v in lab.items():
        if k[1] not in v3: continue
        if v == "rebut":
            t = GEN3.get(k)
            if t is None: continue
            out[k] = "rebut" if bool(HEDGE.search(t)) == hedged else "other"
        else: out[k] = v
    return out
HG = {}
for jn in ("haiku", "silver", "codex"):
    for hedged, tag in ((False, "unhedged"), (True, "hedged")):
        lab = hedge_lab(J[jn], hedged)
        for sn, ms in (("all", ALLM), ("know", KN)):
            for c in ("plain", "premise", "cutoff_date") if jn == "haiku" else ("plain",):
                HG[f"{jn}|{tag}|{sn}|{c}"] = J_of(lab, c, ms)
# share of rebuttals that are hedged, per arm (primary judge, Plain, all models)
for arm in ("P3_NEW", "P3_ANC", "P3_SWAP"):
    ks = [(m, TRI[p][arm], "plain", "T2") for p in PAIRS for m in ALLM]
    rb = [k for k in ks if J["haiku"].get(k) == "rebut" and k in GEN3]
    HG[f"share_hedged|{arm}"] = dict(n=len(rb), share=float(np.mean([bool(HEDGE.search(GEN3[k])) for k in rb])) if rb else None)
R3["hedge"] = HG

# ---------- 1 RAG-fresh + premise-check
RP = {}
pmN = {m: PMR.get(f"{m}|premise_ragf", {}).get("P3_NEW") for m in ALLM}
RP["per_model_new"] = pmN
RP["median_new"] = float(np.median([v for v in pmN.values() if v is not None]))
RP["know"] = J_of(J["haiku"], "premise_ragf", KN)
RP["all"] = J_of(J["haiku"], "premise_ragf", ALLM)
RP["know_plain"] = J_of(J["haiku"], "plain", KN)
FORM = re.compile(r"false premise", re.I)
INSUFF = re.compile(r"no (specific |additional )?(information|mention|details?)|does not (mention|provide|specify|say|state|include|list|contain)|"
                    r"doesn't (mention|provide|specify|say|state|include|list)|not (mentioned|provided|specified|stated|listed)|"
                    r"only (mentions|states|says|provides)|insufficient|not enough information", re.I)
cat = collections.Counter(); bym = collections.Counter()
for p in PAIRS:
    for m in ALLM:
        k = (m, TRI[p]["P3_NEW"], "premise_ragf", "T2")
        if J["haiku"].get(k) != "rebut": continue
        t = GEN3.get(k, ""); cat["n"] += 1; bym[m] += 1
        if FORM.search(t[:100]): cat["formula"] += 1
        if INSUFF.search(t): cat["evidence_insufficient"] += 1
        if INSUFF.search(t) and m in ("qwen2.5-0.5b", "qwen2.5-1.5b"): cat["insufficient_small_qwen"] += 1
RP["rebuttal_text"] = dict(cat); RP["rebuttals_by_model"] = dict(bym)
RP["n_cells"] = len(PAIRS) * len(ALLM)
for jn in ("silver", "codex"):
    t = TR.get(f"{jn}|all|premise_ragf")
    if t: RP[f"{jn}"] = {k: t[k] for k in ("rate_P3_NEW", "rate_P3_ANC", "rate_P3_SWAP")}
    t = TR.get(f"{jn}|know|premise_ragf")
    if t: RP[f"{jn}_know"] = {k: t[k] for k in ("rate_P3_NEW", "rate_P3_ANC", "rate_P3_SWAP")}
R3["ragf_pc"] = RP

# ---------- 2 larger models vs the four knowledgeable small models
LGc = {}
for c in ("plain", "premise", "cutoff_date"):
    LGc[f"know|{c}"] = dict(NEW_post=MG.get(f"{PRIMARY}|know|{c}|NEW_post", {}).get("mean"), OLD=MG.get(f"{PRIMARY}|know|{c}|OLD", {}).get("mean"),
                            **{k: v for k, v in J_of(J["haiku"], c, KN).items() if not k.endswith("_model")})
    for m in KN:
        X = mat_ids(J[PRIMARY], c, G["NEW_post"], [m]); Y = mat_ids(J[PRIMARY], c, G["OLD"], [m])
        LGc[f"{m}|{c}"] = dict(NEW_post=float(np.nanmean(X)), OLD=float(np.nanmean(Y)), P3_NEW=PMR.get(f"{m}|{c}", {}).get("P3_NEW"))
R3["large_vs_know"] = LGc

# ---------- 4 SWAP control: popularity and plausibility
sl = lambda p, c: v3[TRI[p][c]].get("x_sl_wd") or 0
know_rate = lambda p, c, cond="plain": float(np.nanmean(mat_ids(J["haiku"], cond, [TRI[p][c]], KN)))
SW = {}
for c in ("P3_NEW", "P3_ANC", "P3_SWAP"):
    x = [math.log1p(sl(p, c)) for p in PAIRS]; y = [know_rate(p, c) for p in PAIRS]
    r = stats.spearmanr(x, y); SW[f"spearman|{c}"] = dict(rho=float(r.statistic), p=float(r.pvalue), n=len(PAIRS))
SW["n_swap_more_famous"] = int(sum(sl(p, "P3_SWAP") > sl(p, "P3_NEW") for p in PAIRS))
SW["n_former_more_famous"] = int(sum(sl(p, "P3_ANC") > sl(p, "P3_NEW") for p in PAIRS))
le = {p for p in PAIRS if sl(p, "P3_SWAP") <= sl(p, "P3_NEW")}
for sn, ms in (("all", ALLM), ("know", KN)):
    SW[f"swap_le_new|{sn}"] = J_of(J["haiku"], "plain", ms, le)
    SW[f"swap_gt_new|{sn}"] = J_of(J["haiku"], "plain", ms, set(PAIRS) - le)
CF = os.path.join(R, "data", "raw", "wd_country_v3.json")
if os.path.exists(CF):
    CTRY = json.load(open(CF))
    comp = set()
    for p in PAIRS:
        n_, s_ = v3[TRI[p]["P3_NEW"]], v3[TRI[p]["P3_SWAP"]]
        if set(CTRY.get(s_["x"], [])) & (set(CTRY.get(n_["x"], [])) | set(CTRY.get(n_["y"], []))): comp.add(p)
    SW["compatible_pairs"] = sorted(comp)
    SW["compatible_entities"] = sorted(v3[TRI[p]["P3_NEW"]]["y_l"] for p in comp)
    SW["n_missing_country"] = int(sum(1 for p in PAIRS if not CTRY.get(v3[TRI[p]["P3_SWAP"]]["x"])))
    for sn, ms in (("all", ALLM), ("know", KN)):
        SW[f"compatible|{sn}"] = J_of(J["haiku"], "plain", ms, comp)
        SW[f"incompatible|{sn}"] = J_of(J["haiku"], "plain", ms, set(PAIRS) - comp)
# linear probability model: rebut ~ arm + log person sitelinks + model FE + entity FE (Plain, primary judge), clustered by entity
try:
    import pandas as pd, statsmodels.formula.api as smf
    for sn, ms in (("all", ALLM), ("know", KN)):
        rows = []
        for p in PAIRS:
            for c in ("P3_NEW", "P3_ANC", "P3_SWAP"):
                for m in ms:
                    k = (m, TRI[p][c], "plain", "T2")
                    if k in J["haiku"]: rows.append(dict(rebut=int(J["haiku"][k] == "rebut"), arm=c, lpx=math.log1p(sl(p, c)), model=m, ent=p))
        df = pd.DataFrame(rows); df["cl"] = pd.factorize(df["ent"])[0]
        fit = smf.ols("rebut ~ C(arm, Treatment('P3_NEW')) + lpx + C(model) + C(ent)", df).fit(cov_type="cluster", cov_kwds={"groups": df["cl"]})
        g = lambda k: dict(coef=float(fit.params[k]), p=float(fit.pvalues[k]), ci=[float(x) for x in fit.conf_int().loc[k]])
        SW[f"lpm|{sn}"] = dict(Jfam_adj=g("C(arm, Treatment('P3_NEW'))[T.P3_ANC]"), Junf_adj=g("C(arm, Treatment('P3_NEW'))[T.P3_SWAP]"), lpx=g("lpx"), n=len(df))
except Exception as e:
    SW["lpm_error"] = repr(e)
R3["swap"] = SW

# ---------- 6 statistics: Holm over the two Plain J's and over the Table-1 family; held-out-labeller p's
def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (m - r) * ps[i])); adj[i] = run
    return adj.tolist()
pl = TR[f"{PRIMARY}|all|plain"]
ST = dict(plain_t=[pl["Jfam_model"]["t_p"], pl["Junf_model"]["t_p"]], plain_w=[pl["Jfam_model"]["wilcoxon_p"], pl["Junf_model"]["wilcoxon_p"]])
ST["plain_holm"] = holm(ST["plain_t"])
fam = [TR[f"{PRIMARY}|all|{c}"][f"{j}_model"]["t_p"] for c in CONDS for j in ("Jfam", "Junf") if f"{PRIMARY}|all|{c}" in TR and f"{j}_model" in TR[f"{PRIMARY}|all|{c}"]]
ST["table1_n"] = len(fam); ST["table1_min_raw"] = float(min(fam)); ST["table1_min_holm"] = float(min(holm(fam)))
ST["table1_n_sig_holm"] = int(sum(x < .05 for x in holm(fam)))
for jn in ("silver", "codex"):
    t = TR.get(f"{jn}|all|plain")
    if t: ST[f"{jn}_plain_p"] = [t["Jfam_model"]["t_p"], t["Junf_model"]["t_p"]]
ST["n_zero_models_plain"] = int(sum(1 for x in pl["Jfam_model"]["per_model"] if x == 0))
gm = MG.get(f"{PRIMARY}|plain|new_minus_old_model", {}); ST["new_old_t"] = gm.get("t_p"); ST["new_old_w"] = gm.get("wilcoxon_p")
R3["stats"] = ST

# ---------- 7 main-grid groups on T2 only
T2G = {}
for g in ("NEW_post", "NEW_near", "OLD", "STR_early", "STR_late", "STALE_POST", "NEVER"):
    ids = [i for i in G[g] if ALL[i]["template"] == "T2"]
    X = mat_ids(J[PRIMARY], "plain", ids, ALLM)
    T2G[g] = dict(n=len(ids), mean=float(np.nanmean(X)) if ids else None,
                  ci=boot(lambda mi, ii, X=X: np.nanmean(X[ii % X.shape[0]][:, mi]), len(ALLM), X.shape[0]) if ids else None)
XN = mat_ids(J[PRIMARY], "plain", [i for i in G["NEW_post"] if ALL[i]["template"] == "T2"], ALLM)
XO = mat_ids(J[PRIMARY], "plain", [i for i in G["OLD"] if ALL[i]["template"] == "T2"], ALLM)
d = np.nanmean(XN, 0) - np.nanmean(XO, 0)
T2G["new_minus_old_model"] = dict(t_p=float(stats.ttest_1samp(d, 0).pvalue), wilcoxon_p=float(stats.wilcoxon(d).pvalue), n_pos=int((d > 0).sum()))
T2G["template_counts"] = {g: dict(collections.Counter(ALL[i]["template"] for i in G[g])) for g in ("NEW_post", "OLD", "STR_early", "STR_late", "STALE_POST", "NEVER")}
R3["t2_groups"] = T2G

# ---------- 8 256-token Plain re-run of the triples (4 knowledgeable models, primary judge)
LH3 = {k: ("cannot_verify" if v == "refuse" else v) for k, v in load_raw("claude-haiku-5-5", want_long=True).items()}
if LH3:
    lm = sorted({k[0] for k in LH3}, key=lambda m: KN.index(m) if m in KN else 99)
    R3["long_triples"] = dict(models=lm, short=J_of(J["haiku"], "plain", lm), long=J_of(LH3, "plain", lm),
                              same_label=float(np.mean([J["haiku"][k] == v for k, v in LH3.items() if k in J["haiku"] and k[1] in v3])),
                              n=int(sum(1 for k in LH3 if k[1] in v3)))
    GEN3_backup = GEN3
    GEN3 = {**GEN3, **{k: v for k, v in GENL.items()}}   # hedge regex on the long texts for the long labels
    R3["long_triples"]["long_unhedged"] = J_of(hedge_lab(LH3, False), "plain", lm)
    GEN3 = GEN3_backup

# ---------- 10 Qwen3.5-4B per model (main grid; it ran Plain, Premise-check and Policy only; never pooled)
Q35 = {}
for c in ("plain", "premise", "policy"):
    for g in ("NEW_post", "NEW_near", "OLD", "STR_early", "NEVER"):
        X = mat_ids(J[PRIMARY], c, G[g], ["qwen3.5-4b"])
        if X.size and not np.all(np.isnan(X)): Q35[f"{c}|{g}"] = float(np.nanmean(X))
for yr in ("2025", "2026"):
    ids = [i for i in G["NEW_post"] if ALL[i]["t_change"][:4] == yr]
    X = mat_ids(J[PRIMARY], "plain", ids, ["qwen3.5-4b"])
    if X.size and not np.all(np.isnan(X)): Q35[f"plain|NEW_{yr}"] = float(np.nanmean(X)); Q35[f"n_NEW_{yr}"] = len(ids)
R3["qwen35"] = Q35

# ---------- 10 refined invented-tenure regex (the role's head noun must occur in the same sentence as the dated tenure)
def head(role):
    h = role.split(" of ")[0].lower()
    return h.split()[-1] if h.split() else h
inv = 0; n = 0
for k, lab_ in J[PRIMARY].items():
    if k[2] != "plain" or k[1] not in items or group(items[k[1]]) != "NEW_post" or lab_ != "rebut" or k[0] not in ALLM: continue
    it = items[k[1]]; t = gens.get(k, ""); n += 1; sur = it["x_l"].split()[-1].lower(); hw = head(it["role_full"])
    for sent in re.split(r"(?<=[.;])\s+", t):
        if re.search(r"\b(served|was|has been|had been)\b[^.]{0,60}\b(19|20)\d\d\b", sent) and hw in sent.lower() and sur in t.lower():
            inv += 1; break
R3["invented_tenure_strict"] = dict(n=n, k=inv)

# ---------- 9 item notes: NEW dates of the form 1 January (possibly year precision); SWAP persons that are excluded NEW holders
R3["jan1_new_triples"] = int(sum(1 for p in PAIRS if v3[TRI[p]["P3_NEW"]]["t_change"].endswith("-01-01")))
R3["jan1_new_post"] = int(sum(1 for i in G["NEW_post"] if ALL[i]["t_change"].endswith("-01-01")))
exl_names = {it["x_l"] for i_, it in map(lambda l: (None, json.loads(l)), open(os.path.join(R, "data", "items.jsonl"))) if it["id"] in EXCL}
R3["swap_is_excluded_holder"] = sorted(v3[TRI[p]["P3_SWAP"]]["x_l"] for p in PAIRS if v3[TRI[p]["P3_SWAP"]]["x_l"] in exl_names)
res["r3"] = R3
print("r3 ok:", {k: (v if not isinstance(v, dict) else len(v)) for k, v in R3.items() if k != "swap"})
