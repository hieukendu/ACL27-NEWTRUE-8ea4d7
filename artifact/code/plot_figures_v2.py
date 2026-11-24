"""Revised figures (round 1) from results/analysis/v2.json:
fig_tradeoff.pdf  (a) conditions in (rebut NEW-post, rebut paired ANC) space, all models, primary judge, two-level CIs;
                  (b) mean P(No) per model for OLD / NEW-post / STR-early (audited items)
fig_pop.pdf       Plain rebuttals of NEW-post vs OLD premises by entity-popularity tertile (all models, primary judge)"""
import json, os, sys, glob, math, collections
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from plotstyle import *
R = os.path.join(os.path.dirname(__file__), ".."); F = os.path.join(R, "figures")
setup_warm()
V = json.load(open(os.path.join(R, "results", "analysis", "v2.json")))
J0 = V["primary_judge"]; PA = V["paired_anc"]
V3 = json.load(open(os.path.join(R, "results", "analysis", "v3.json"))); T3 = V3["triples"]; J3 = V3["primary"]
# 2026-11-20: redrawn at column width in the warm style of Figure 1; (a) above (b). Colour = kind of intervention:
# ink = neither a premise check nor evidence, brown = a premise-check instruction, amber = retrieved evidence only.
CONDS = [("plain", "Plain"), ("premise", "Premise-check"), ("premise_fq", "PC (FreshQA)"), ("date", "Date"), ("cutoff_date", "Cutoff-stated"),
         ("rag_fresh", "RAG-fresh"), ("premise_ragf", "RAG-fresh+PC"), ("rag_mixed_u", "RAG-mixed"), ("rag_stale_u", "RAG-stale"), ("policy", "Policy")]
COL = {"premise": W_BROWN, "premise_fq": W_BROWN, "premise_ragf": W_BROWN, "rag_fresh": W_AMBER, "rag_mixed_u": W_AMBER, "rag_stale_u": W_AMBER}
# label anchor (x, y in data units) and horizontal alignment, placed by hand to avoid collisions at 7 pt
LAB = {"plain": (33.5, 39.5, "left"), "premise": (59, 75, "right"), "premise_fq": (32, 47, "left"), "date": (21.5, 34.5, "right"),
       "cutoff_date": (14.5, 16.5, "left"), "rag_fresh": (3, 48, "left"), "premise_ragf": (42, 88.5, "left"), "rag_mixed_u": (7, 61, "left"),
       "rag_stale_u": (52, 54.5, "left"), "policy": (17, 27.5, "right")}
setup_warm()
fig = plt.figure(figsize=(COL_W, 10.0 * CM))
a1 = fig.add_axes([1.0 / 7.7, 4.2 / 10.0, 6.45 / 7.7, 5.5 / 10.0])
a2 = fig.add_axes([2.55 / 7.7, 0.85 / 10.0, 4.9 / 7.7, 2.05 / 10.0])
a1.plot([0, 100], [0, 100], color=W_MUTED, lw=0.6, zorder=1)
for c, name in CONDS:
    t = T3.get(f"{J3}|all|{c}")
    if not t: continue
    x, ya, ys = 100 * t["rate_P3_NEW"], 100 * t["rate_P3_ANC"], 100 * t["rate_P3_SWAP"]
    col = COL.get(c, W_INK)
    a1.plot([x, x], [ya, ys], color=col, lw=0.8, zorder=2)
    a1.plot(x, ya, "o", ms=4.4, color=col, mec="white", mew=0.7, zorder=4)
    a1.plot(x, ys, "o", ms=4.0, mfc="white", mec=col, mew=1.0, zorder=4)
    lx, ly, ha = LAB[c]
    a1.text(lx, ly, name, fontsize=7, color=W_INK, ha=ha, va="center", zorder=5)
a1.plot([], [], "o", ms=4.4, color=W_INK, mec="white", label="former holder (familiar)")
a1.plot([], [], "o", ms=4.0, mfc="white", mec=W_INK, mew=1.0, label="swapped holder (unfamiliar)")
a1.legend(loc="lower right", handletextpad=0.2, borderaxespad=0.2, labelspacing=0.3, title="false premise:", title_fontsize=7, alignment="left")
a1.set_xlim(-3, 103); a1.set_ylim(-3, 103); a1.set_xticks(range(0, 101, 20)); a1.set_yticks(range(0, 101, 20))
fig.canvas.draw()
p0, p1 = a1.transData.transform([(0, 0), (100, 100)]); ang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
a1.text(80, 82.5, "rebutted equally often", rotation=ang, rotation_mode="anchor", fontsize=7, color=W_MUTED, ha="center", va="bottom")
a1.set_xlabel("rebuts the newly-true premise (%)"); a1.set_ylabel("rebuts a false premise, same entity (%)")
VB = V["belief"]; ms = [m for m in MODEL_ORDER if m in VB and m in V3["models_all"]]   # round 3: the 7 pooled models only
groups = [("OLD", "Old (true)"), ("NEW_post", "New-post (true)"), ("STR_early", "Stale <2021 (false)")]
for j, (g, lab) in enumerate(groups):
    vals = [VB[m][g] for m in ms if g in VB[m]]
    a2.scatter(vals, [j] * len(vals), s=13, color=W_BROWN, zorder=3, edgecolor="white", linewidth=0.6)
    a2.plot([np.mean(vals)] * 2, [j - 0.32, j + 0.32], color=W_INK, lw=1.3, zorder=4, solid_capstyle="butt")
a2.set_yticks(range(len(groups))); a2.set_yticklabels([l for _, l in groups]); a2.grid(axis="y", visible=False)
a2.tick_params(axis="y", length=0); a2.set_ylim(-0.55, len(groups) - 0.45)
a2.set_xlabel("mean P(No) to “Is it true that x is the r?”"); a2.set_xlim(0.3, 1.02)
a2.set_xticks([0.3, 0.5, 0.7, 0.9]); a2.set_xticklabels(["0.3", "0.5", "0.7", "0.9"])
fig.text(0.012, 0.985, "a", fontsize=8, weight="bold", va="top"); fig.text(0.012, 3.05 / 10.0, "b", fontsize=8, weight="bold", va="top")
fig.savefig(os.path.join(F, "fig_tradeoff.pdf"), metadata={"CreationDate": None})

# popularity figure (Plain, primary judge): tertiles of entity sitelinks over NEW_post + OLD items, all models
EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl"))) if i["id"] not in EXCL}
lab = {}
for f in glob.glob(os.path.join(R, "results", "labels", "claude-haiku-5-5", "*.jsonl")):
    if any(s in f for s in ("_sweep", "_long", "_anc")): continue
    for l in open(f):
        r = json.loads(l); lab[(r["model"], r["id"], r["icond"], r["template"])] = r["label"]
grp = lambda it: ("NEW_post" if it["cond"] == "NEW" and it["t_change"] >= "2025-01-01" else ("OLD" if it["cond"] == "OLD" else None))
ids = [i for i, it in items.items() if grp(it)]
cuts = np.percentile([items[i]["y_sl"] for i in ids], [33.3, 66.7])
tert = lambda s: 0 if s <= cuts[0] else (1 if s <= cuts[1] else 2)
rng = np.random.default_rng(3)
fig = plt.figure(figsize=(COL_W, 4.6 * CM)); ax = fig.add_axes([1.05 / 7.7, 0.95 / 4.6, 5.0 / 7.7, 3.45 / 4.6])
END = []
for k, (g, name) in enumerate((("NEW_post", "newly-true"), ("OLD", "long-true"))):
    ys, lo, hi = [], [], []
    for t in range(3):
        per = collections.defaultdict(list)
        for i in ids:
            if grp(items[i]) == g and tert(items[i]["y_sl"]) == t:
                for m in V["models_all"]:
                    kk = (m, i, "plain", items[i]["template"])
                    if kk in lab: per[i].append(lab[kk] == "rebut")
        keys = list(per); vals = [np.mean(per[i]) for i in keys]
        ys.append(100 * np.mean(vals)); bs = [100 * np.mean([vals[j] for j in rng.integers(0, len(vals), len(vals))]) for _ in range(1000)]
        lo.append(ys[-1] - np.percentile(bs, 2.5)); hi.append(np.percentile(bs, 97.5) - ys[-1])
    col = [W_BROWN, W_AMBER][k]
    ax.errorbar(np.arange(3) + (k - 0.5) * 0.1, ys, yerr=[lo, hi], fmt="o-", ms=3.6, color=col, mec="white", mew=0.5, label=name,
                elinewidth=0.9, capsize=0, lw=1.2, zorder=3 + k)
    END.append((ys[-1], name, k))
for y, name, k in END:   # direct labels at the line ends (ink text, coloured mark beside it)
    ax.text(2 + (k - 0.5) * 0.1 + 0.16, y, name, fontsize=7, color=W_INK, va="center", ha="left")
ax.set_xticks(range(3)); ax.set_xticklabels(["low", "mid", "high"]); ax.set_xlabel("entity popularity (sitelink tertile)")
ax.set_xlim(-0.25, 2.2); ax.grid(axis="x", visible=False)
ax.set_ylabel("rebutted under Plain (%)"); ax.set_ylim(0, 70); ax.set_yticks(range(0, 71, 20))
fig.savefig(os.path.join(F, "fig_pop.pdf"), metadata={"CreationDate": None})
print("v2 figures ok")
