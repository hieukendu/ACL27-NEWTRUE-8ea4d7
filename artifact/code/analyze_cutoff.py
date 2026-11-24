"""Estimate effective knowledge cutoff from date-probe results with a step-function change-point model:
P(prefer new holder) = p1 for changes before c, p2 after c. c maximizes the Bernoulli likelihood over a monthly grid.
95% CI via bootstrap over probe transitions (500 resamples). Writes results/analysis/cutoffs.json"""
import json, os, glob, math, random, datetime as dt
import numpy as np
R = os.path.join(os.path.dirname(__file__), "..")
def months(d): return int(d[:4]) * 12 + int(d[5:7]) - 1
def mstr(m): return f"{m // 12}-{m % 12 + 1:02d}"
GRID = list(range(months("2020-06-01"), months("2026-06-01") + 1))

def fit(t, y):
    best = (-1e18, None)
    for c in GRID:
        a = y[t < c]; b = y[t >= c]
        if len(a) < 20 or len(b) < 20: continue
        ll = 0
        for s in (a, b):
            p = min(max(s.mean(), 1e-3), 1 - 1e-3); ll += (s * math.log(p) + (1 - s) * math.log(1 - p)).sum()
        if ll > best[0]: best = (ll, c, a.mean(), b.mean())
    return best

out = {}
for f in sorted(glob.glob(os.path.join(R, "results", "probe", "*.jsonl"))):
    name = os.path.basename(f)[:-6]
    P = [json.loads(l) for l in open(f)]
    t = np.array([months(p["t_change"]) for p in P]); y = np.array([float(p["lp_new"] > p["lp_old"]) for p in P])
    ll, c, p1, p2 = fit(t, y)
    rng = np.random.default_rng(0); bs = []
    for _ in range(500):
        idx = rng.integers(0, len(t), len(t)); r = fit(t[idx], y[idx]); bs.append(r[1])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    # null check: likelihood-ratio vs constant model
    p0 = y.mean(); ll0 = (y * math.log(p0) + (1 - y) * math.log(1 - p0)).sum()
    # permutation test of the max-LLR statistic (change-point search included), 200 permutations
    perm = []
    for _ in range(200):
        yp = rng.permutation(y); r = fit(t, yp)
        perm.append(2 * (r[0] - ll0))
    perm_p = (1 + sum(v >= 2 * (ll - ll0) for v in perm)) / 201
    halfs = {}
    for p, yy in zip(P, y):
        k = p["t_change"][:4] + ("H1" if p["t_change"][5:7] <= "06" else "H2"); halfs.setdefault(k, []).append(yy)
    out[name] = dict(cutoff=mstr(c), ci=[mstr(int(lo)), mstr(int(hi))], p_before=p1, p_after=p2, llr=2 * (ll - ll0), perm_p=perm_p, n=len(P),
                     by_half={k: [float(np.mean(v)), len(v)] for k, v in sorted(halfs.items())})
    print(name, out[name]["cutoff"], out[name]["ci"], round(p1, 2), round(p2, 2), "LLR", round(2 * (ll - ll0), 1), "perm p", round(perm_p, 3))
json.dump(out, open(os.path.join(R, "results", "analysis", "cutoffs.json"), "w"), indent=1)
