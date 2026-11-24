"""All data figures from results/analysis/main.json (+ cutoffs.json)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from plotstyle import *
R = os.path.join(os.path.dirname(__file__), "..")
F = os.path.join(R, "figures")
setup()
M = json.load(open(os.path.join(R, "results", "analysis", "main.json")))
P, T = M["pooled"], M["table"]
CONDS = ["plain", "premise", "date", "rag_fresh", "rag_stale", "policy", "policy_nodate"]
SHORT = {"plain": "Plain", "premise": "Premise-check", "date": "Date", "rag_fresh": "RAG-fresh", "rag_stale": "RAG-stale",
         "policy": "Policy", "policy_nodate": "Policy-nodate"}
models = [m for m in MODEL_ORDER if m in M["models"]]

# ---- Fig 2: trade-off (pooled) + per-model verifier curves
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.5), gridspec_kw={"width_ratios": [1.15, 1]})
PID = M["pooled_id"]
for m in M["id_models"]:
    v = M["verifier"].get(f"{m}|plain")
    if not v: continue
    c = np.array(v["curve_never"]); a1.plot(100 * c[:, 0], 100 * c[:, 1], color="#b9b7b0", lw=0.7, zorder=1)
a1.plot([], [], color="#b9b7b0", lw=0.7, label="P(No) threshold sweep, per model")
a1.plot([0, 100], [0, 100], color=INK2, lw=0.6, ls=":", zorder=1)
a1.text(88, 79, "chance", rotation=36, fontsize=5.5, color=INK2, ha="center")
OFF = {"plain": (4, -8), "premise": (-38, 5), "date": (-14, -10), "rag_fresh": (4, 2), "rag_stale": (-30, 6), "policy": (4, -2), "policy_nodate": (4, -8)}
for k, c in enumerate(CONDS):
    col = SERIES[1] if c == "premise" else (SERIES[2] if c.startswith("policy") else (SERIES[3] if c.startswith("rag") else SERIES[0]))
    xa, ya = P[f"{c}|NEW_post|rebut"], P[f"{c}|NEVER|rebut"]
    a1.plot(100 * xa["mean"], 100 * ya["mean"], "o", ms=4, mfc="none", mec=col, mew=0.8, zorder=3)
    a1.plot([100 * xa["mean"], 100 * PID[f"{c}|NEW_post|rebut"]["mean"]], [100 * ya["mean"], 100 * PID[f"{c}|NEVER|rebut"]["mean"]], color=col, lw=0.4, zorder=2)
    x = PID[f"{c}|NEW_post|rebut"]; y = PID[f"{c}|NEVER|rebut"]
    a1.errorbar(100 * x["mean"], 100 * y["mean"], xerr=[[100 * (x["mean"] - x["ci"][0])], [100 * (x["ci"][1] - x["mean"])]],
                yerr=[[100 * (y["mean"] - y["ci"][0])], [100 * (y["ci"][1] - y["mean"])]], fmt="o", ms=4.5, color=col,
                ecolor=col, elinewidth=0.8, capsize=0, zorder=4, mec="white", mew=0.8)
    a1.annotate(SHORT[c], (100 * x["mean"], 100 * y["mean"]), xytext=OFF[c], textcoords="offset points", fontsize=6.0, color=INK, zorder=5)
a1.plot([], [], "o", ms=4.5, color=INK2, label=f"identified-cutoff models ({len(M['id_models'])})")
a1.plot([], [], "o", ms=4, mfc="none", mec=INK2, label=f"all models ({len(M['full_models'])})")
a1.set_xlabel("false-rebuttal rate on NEW-post true premises (%)")
a1.set_ylabel("catch rate on NEVER-true premises (%)")
a1.set_xlim(-2, 102); a1.set_ylim(-2, 102); a1.legend(loc="lower right", fontsize=5.6)
a1.set_title("(a) Interventions, pooled (95% CI)")
# (b) mean P(No) by condition for the verifier, per model (dot plot)
groups = [("OLD", "Old (true)"), ("NEW_post", "New-post (true)"), ("STALE_PRE", "Stale-pre (false)"), ("NEVER", "Never (false)")]
ms = [m for m in models if f"{m}|plain" in M["verifier"]]
for j, (g, lab) in enumerate(groups):
    vals = [M["verifier"][f"{m}|plain"]["mean_pno"][g] for m in ms]
    a2.scatter(vals, [j] * len(vals), s=14, color=SERIES[j if j < 3 else 7], zorder=3, edgecolor="white", linewidth=0.5)
    a2.plot([np.mean(vals)] * 2, [j - 0.3, j + 0.3], color=INK, lw=1.4, zorder=4)
a2.set_yticks(range(len(groups))); a2.set_yticklabels([l for _, l in groups])
a2.set_xlabel("mean P(No) to “Is it true that x is the role?”")
a2.set_xlim(0.35, 1.02); a2.set_title("(b) Model belief: new-true looks false")
a2.grid(axis="y", visible=False)
fig.tight_layout(pad=0.4); fig.savefig(os.path.join(F, "fig_tradeoff.pdf"))

# ---- Fig 3: per-model trade-off small multiples (appendix)
fig, axes = plt.subplots(2, 4, figsize=(7.0, 3.6), sharex=True, sharey=True)
for ax, m in zip(axes.flat, models):
    v = M["verifier"].get(f"{m}|plain")
    if v:
        c = np.array(v["curve_never"]); ax.plot(100 * c[:, 0], 100 * c[:, 1], color="#b9b7b0", lw=0.7)
    pts = [(c, T.get(f"{m}|{c}|NEW_post|rebut"), T.get(f"{m}|{c}|NEVER|rebut")) for c in CONDS]
    for c, x, y in pts:
        if not x or x["mean"] is None or not y or y["mean"] is None: continue
        col = SERIES[1] if c == "premise" else (SERIES[2] if c.startswith("policy") else SERIES[0])
        ax.plot(100 * x["mean"], 100 * y["mean"], "o", ms=3.5, color=col, mec="white", mew=0.5)
        ax.annotate({"plain": "P", "premise": "PC", "date": "D", "rag_fresh": "RF", "rag_stale": "RS", "policy": "Pol", "policy_nodate": "Pnd"}[c],
                    (100 * x["mean"], 100 * y["mean"]), xytext=(2, 2), textcoords="offset points", fontsize=5.2)
    ax.plot([0, 100], [0, 100], color=INK2, lw=0.5, ls=":")
    ax.set_title(PRETTY[m]); ax.set_xlim(-3, 103); ax.set_ylim(-3, 103)
for ax in axes[-1]: ax.set_xlabel("FRR new-post (%)")
for ax in axes[:, 0]: ax.set_ylabel("catch never (%)")
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(F, "fig_tradeoff_permodel.pdf"))

# ---- Fig 4: time since change (pooled) for plain / premise / policy
B = M["breakdowns"]
fig, ax = plt.subplots(figsize=(3.3, 2.1))
for k, c in enumerate(["plain", "premise", "policy"]):
    d = B[f"time|pooled|{c}"]; ks = sorted(d)
    x = [int(h[:4]) + (0.25 if h.endswith("H1") else 0.75) for h in ks]
    y = [100 * d[h]["mean"] for h in ks]; lo = [100 * d[h]["ci"][0] for h in ks]; hi = [100 * d[h]["ci"][1] for h in ks]
    col = [SERIES[0], SERIES[1], SERIES[2]][k]
    ax.plot(x, y, marker="o", ms=3, color=col, label=SHORT[c]); ax.fill_between(x, lo, hi, color=col, alpha=0.12, lw=0)
ax.axvline(2025.0, color=INK2, lw=0.7, ls="--"); ax.text(2025.05, 4, "all cutoffs\nbefore here", fontsize=5.5, color=INK2)
ax.set_xlabel("date the premise became true"); ax.set_ylabel("false rebuttals (%)"); ax.set_ylim(0, 100)
ax.legend(fontsize=6, loc="upper left", ncol=3)
fig.tight_layout(pad=0.3); fig.savefig(os.path.join(F, "fig_time.pdf"))

# ---- Fig 5: scaling within Qwen2.5 + popularity
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.0))
sizes = [("qwen2.5-0.5b", 0.5), ("qwen2.5-1.5b", 1.5), ("qwen2.5-3b", 3), ("qwen2.5-7b", 7)]
for k, c in enumerate(["plain", "premise", "policy"]):
    col = [SERIES[0], SERIES[1], SERIES[2]][k]
    xs = [s for m, s in sizes if f"{m}|{c}|NEW_post|rebut" in T]
    a1.plot(xs, [100 * T[f"{m}|{c}|NEW_post|rebut"]["mean"] for m, s in sizes if f"{m}|{c}|NEW_post|rebut" in T], marker="o", ms=3, color=col, label=f"{SHORT[c]}: FRR new")
    a1.plot(xs, [100 * T[f"{m}|{c}|NEVER|rebut"]["mean"] for m, s in sizes if f"{m}|{c}|NEVER|rebut" in T], marker="s", ms=3, color=col, ls="--", label=f"{SHORT[c]}: catch never")
a1.set_xscale("log"); a1.set_xticks([0.5, 1.5, 3, 7]); a1.set_xticklabels(["0.5B", "1.5B", "3B", "7B"]); a1.minorticks_off()
a1.set_ylabel("rebut rate (%)"); a1.set_ylim(0, 103); a1.set_title("(a) Qwen2.5 size trend (solid: NEW-post true; dashed: NEVER false)")
from matplotlib.lines import Line2D
a1.legend(handles=[Line2D([], [], color=SERIES[k], label=SHORT[c]) for k, c in enumerate(["plain", "premise", "policy"])], fontsize=5.6, loc="center right")
for k, c in enumerate(["plain", "premise", "policy"]):
    d = B[f"pop|{c}|NEW_all"]; ks = ["low", "mid", "high"]
    a2.errorbar(np.arange(3) + (k - 1) * 0.12, [100 * d[q]["mean"] for q in ks],
                yerr=[[100 * (d[q]["mean"] - d[q]["ci"][0]) for q in ks], [100 * (d[q]["ci"][1] - d[q]["mean"]) for q in ks]],
                fmt="o", ms=3.5, color=[SERIES[0], SERIES[1], SERIES[2]][k], label=SHORT[c], elinewidth=0.8)
a2.set_xticks(range(3)); a2.set_xticklabels(["low", "mid", "high"]); a2.set_xlabel("entity popularity (sitelink tertile)")
a2.set_ylabel("rebut true NEW (%)"); a2.set_ylim(0, 100); a2.set_title("(b) Entity popularity, all models (all NEW items)"); a2.legend(fontsize=6, loc="upper left")
fig.tight_layout(pad=0.4); fig.savefig(os.path.join(F, "fig_scaling_pop.pdf"))
print("figures ok")
