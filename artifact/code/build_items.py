"""Build the frozen evaluation items (snapshot 2026-11-10) and the cutoff-probe set.
Conditions: NEW (true, changed 2023-07..2026-10), STALE_POST (old holder of a NEW-entity, changed >=2025),
STALE_PRE (old holder, changed 2019-01..2022-06), OLD (holder since <=2021, still current), NEVER (holder swapped
from another entity of the same relation; never held this role per Wikidata)."""
import json, os, random, collections, datetime as dt
D = os.path.join(os.path.dirname(__file__), "..", "data")
rng = random.Random(20261110)
ROLE = {"P6": "head of government", "P35": "head of state", "P169": "CEO", "P286": "head coach", "P488": "chairperson"}

def role_full(rel, office, ent_l):
    if rel in ("P6", "P35") and office and len(office) < 60:
        return office
    return f"{ROLE[rel]} of {ent_l}"

def fmt(d):
    x = dt.date.fromisoformat(d); return f"{x.day} {x.strftime('%B')} {x.year}"

def half(d): return f"{d[:4]}H{1 if d[5:7] <= '06' else 2}"

def ok_label(s): return s and len(s) < 70 and not s.startswith("Q") and "," not in s[:3]

T = [json.loads(l) for l in open(os.path.join(D, "transitions.jsonl"))]
O = [json.loads(l) for l in open(os.path.join(D, "oldtrue.jsonl"))]
allh = json.load(open(os.path.join(D, "all_holders.json")))
T = [t for t in T if ok_label(t["ent_l"]) and ok_label(t["new_l"]) and ok_label(t["old_l"]) and t["old_sl"] >= 8 and t["new_sl"] >= 4]
# dedupe: same (new holder, office/role) across entities (e.g., England / United Kingdom)
seen, T2 = set(), []
for t in sorted(T, key=lambda t: -t["ent_sl"]):
    k = (t["new"], t["old"], t["t_change"])
    if k in seen: continue
    seen.add(k); T2.append(t)
T = T2
recent_ents = {(t["rel"], t["ent"]) for t in T if t["t_change"] >= "2022-01-01"}

items = []
def add(cond, rel, ent, ent_l, ent_sl, office, x, x_l, x_sl, truth, t_change, cur, cur_l, cur_since, prior, prior_l, extra=None):
    rf = role_full(rel, office, ent_l)
    it = dict(id=f"{cond}-{len(items):04d}", cond=cond, rel=rel, y=ent, y_l=ent_l, y_sl=ent_sl, role_full=rf, x=x, x_l=x_l,
              x_sl=x_sl, truth=truth, t_change=t_change,
              evidence_fresh=f"{cur_l} has been {rf} since {fmt(cur_since)}." if cur_since else f"{cur_l} is {rf}.",
              evidence_stale=f"{prior_l} is {rf}.")
    if extra: it.update(extra)
    items.append(it)

# NEW: stratified by relation x half-year, ent_sl >= 25
pool = collections.defaultdict(list)
for t in T:
    if "2023-07-01" <= t["t_change"] <= "2026-10-31" and t["ent_sl"] >= (10 if t["rel"] == "P169" else 25):
        pool[(t["rel"], half(t["t_change"]))].append(t)
new_sel = []
for k in sorted(pool):
    c = pool[k][:]; rng.shuffle(c); new_sel += c[:(8 if k[0] == "P169" else 6)]
used_ents = set()
for t in new_sel:
    used_ents.add((t["rel"], t["ent"]))
    add("NEW", t["rel"], t["ent"], t["ent_l"], t["ent_sl"], t["office"], t["new"], t["new_l"], t["new_sl"], True,
        t["t_change"], t["new"], t["new_l"], t["t_change"], t["old"], t["old_l"],
        dict(old_l=t["old_l"], old_end=t["old_end"]))
# STALE_POST: matched old holders for NEW entities whose change is >= 2025-01-01
post = [t for t in new_sel if t["t_change"] >= "2025-01-01"]
rng.shuffle(post)
for t in post[:90]:
    add("STALE_POST", t["rel"], t["ent"], t["ent_l"], t["ent_sl"], t["office"], t["old"], t["old_l"], t["old_sl"], False,
        t["t_change"], t["new"], t["new_l"], t["t_change"], t["old"], t["old_l"], dict(new_l=t["new_l"]))
# STALE_PRE: old holder replaced 2019-01..2022-06 and the replacement is still current
pool = collections.defaultdict(list)
for t in T:
    if "2019-01-01" <= t["t_change"] <= "2022-06-30" and t["ent_sl"] >= 25 and (t["rel"], t["ent"]) not in used_ents:
        pool[t["rel"]].append(t)
for rel in sorted(pool):
    c = pool[rel][:]; rng.shuffle(c)
    for t in c[:12]:
        used_ents.add((t["rel"], t["ent"]))
        add("STALE_PRE", t["rel"], t["ent"], t["ent_l"], t["ent_sl"], t["office"], t["old"], t["old_l"], t["old_sl"], False,
            t["t_change"], t["new"], t["new_l"], t["t_change"], t["old"], t["old_l"], dict(new_l=t["new_l"]))
# OLD: holder since 2010..2021, still current, entity had no recorded change since 2022
pool = collections.defaultdict(list)
for o in O:
    if "2010-01-01" <= o["t_start"] <= "2021-12-31" and o["ent_sl"] >= 25 and ok_label(o["ent_l"]) and ok_label(o["holder_l"]) \
            and o["holder_sl"] >= 4 and (o["rel"], o["ent"]) not in recent_ents and (o["rel"], o["ent"]) not in used_ents:
        pool[o["rel"]].append(o)
old_sel, never_ents = [], []
for rel in sorted(pool):
    c = pool[rel][:]; rng.shuffle(c)
    old_sel += c[:16]; never_ents += c[16:28]
for o in old_sel:
    add("OLD", o["rel"], o["ent"], o["ent_l"], o["ent_sl"], o["office"], o["holder"], o["holder_l"], o["holder_sl"], True,
        o["t_start"], o["holder"], o["holder_l"], o["t_start"], o["holder"], o["holder_l"])
# NEVER: swap in the holder of another (long-standing) entity of the same relation
donors = collections.defaultdict(list)
for o in old_sel + never_ents: donors[o["rel"]].append(o)
for o in never_ents:
    cand = [d for d in donors[o["rel"]] if d["ent"] != o["ent"] and d["holder"] not in allh.get(f"{o['rel']}|{o['ent']}", [])
            and d["holder"] != o["holder"]]
    d = rng.choice(cand)
    add("NEVER", o["rel"], o["ent"], o["ent_l"], o["ent_sl"], o["office"], d["holder"], d["holder_l"], d["holder_sl"], False,
        None, o["holder"], o["holder_l"], o["t_start"], o["holder"], o["holder_l"], dict(true_holder_l=o["holder_l"], donor_role=role_full(d["rel"], d["office"], d["ent_l"])))
# template assignment, balanced within condition x relation
TPL = ["T1", "T2", "T3"]
cnt = collections.Counter()
for it in items:
    k = (it["cond"], it["rel"]); it["template"] = TPL[cnt[k] % 3]; cnt[k] += 1
with open(os.path.join(D, "items_candidates.jsonl"), "w") as f:
    for it in items: f.write(json.dumps(it) + "\n")
print(collections.Counter(i["cond"] for i in items))
print(collections.Counter((i["cond"], i["rel"]) for i in items))

# cutoff-probe set: transitions 2019-01..2026-10, ent_sl>=25, stratified by quarter, up to 14 per quarter
pool = collections.defaultdict(list)
for t in T:
    if "2019-01-01" <= t["t_change"] <= "2026-10-31" and t["ent_sl"] >= 25 and t["old"] != t["new"]:
        q = f"{t['t_change'][:4]}Q{(int(t['t_change'][5:7]) - 1) // 3 + 1}"
        pool[q].append(t)
probe = []
for q in sorted(pool):
    c = pool[q][:]; rng.shuffle(c)
    for t in c[:14]:
        probe.append(dict(t, quarter=q, role_full=role_full(t["rel"], t["office"], t["ent_l"])))
with open(os.path.join(D, "probe.jsonl"), "w") as f:
    for p in probe: f.write(json.dumps(p) + "\n")
print("probe", len(probe))
