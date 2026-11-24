"""Figure: date-probe preference for the new holder by half-year of change, with the fitted step
(p_before / p_after at the change point) and its bootstrap 95% CI, from results/analysis/cutoffs.json.
Drawn at ACL column width (7.7 cm) in the warm style of Figure 1 (plotstyle.setup_warm)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from plotstyle import *
R = os.path.join(os.path.dirname(__file__), "..")
setup_warm()
C = json.load(open(os.path.join(R, "results", "analysis", "cutoffs.json")))
ms = [m for m in MODEL_ORDER if m in C]
ym = lambda s: int(s[:4]) + (int(s[5:7]) - 0.5) / 12          # "YYYY-MM" -> decimal year (mid-month)
fig, axes = plt.subplots(4, 2, figsize=(COL_W, 10.6 * CM), sharex=True, sharey=True)
fig.subplots_adjust(left=0.13, right=0.985, top=0.935, bottom=0.08, hspace=0.78, wspace=0.12)
X0, X1 = 2019.0, 2027.0
for ax, m in zip(axes.flat, ms):
    bh = C[m]["by_half"]; ks = sorted(bh)
    x = [int(k[:4]) + (0.25 if k.endswith("H1") else 0.75) for k in ks]; y = [bh[k][0] for k in ks]
    ax.axhline(0.5, color=W_MUTED, lw=0.5, zorder=1)
    sig = C[m].get("perm_p", 1) < 0.05 and C[m]["p_before"] > C[m]["p_after"]
    if sig:
        cx = ym(C[m]["cutoff"]); lo, hi = map(ym, C[m]["ci"])
        ax.axvspan(lo, hi, color=W_AMBER, alpha=0.32, lw=0, zorder=0)
        ax.plot([X0, cx, cx, X1], [C[m]["p_before"], C[m]["p_before"], C[m]["p_after"], C[m]["p_after"]], color=W_INK, lw=0.8, zorder=3)
        sub = f"step {C[m]['cutoff']}"
    else:
        sub = "no reliable step"
    ax.plot(x, y, color=W_BROWN, lw=1.0, marker="o", ms=2.2, mec="white", mew=0.3, zorder=4)
    ax.annotate(PRETTY[m], (0, 1), xytext=(0, 10.5), textcoords="offset points", xycoords="axes fraction", fontsize=7, color=W_INK, va="bottom", weight="bold")
    ax.annotate(sub, (0, 1), xytext=(0, 2.5), textcoords="offset points", xycoords="axes fraction", fontsize=7, color=W_INK if sig else W_MUTED, va="bottom")
    ax.set_xlim(X0, X1); ax.set_ylim(0, 1); ax.set_yticks([0, 0.5, 1]); ax.set_yticklabels(["0", ".5", "1"])
    ax.set_xticks([2019, 2021, 2023, 2025]); ax.set_xticklabels(["’19", "’21", "’23", "’25"])
    ax.grid(axis="x", visible=False)
fig.supylabel("share preferring the new holder", fontsize=7, x=0.01)
fig.supxlabel("date of change (half-year)", fontsize=7, y=0.005)
fig.savefig(os.path.join(R, "figures", "fig_cutoff.pdf"), metadata={"CreationDate": None})
print("ok")
