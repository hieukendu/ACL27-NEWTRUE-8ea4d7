"""Round-1 addition: an entity-matched, plausible, knowable-false control (STALE_ANCIENT).
For every NEW-post item (role became true on/after 2025-01-01) we take, from the same frozen Wikidata dump, a former holder
of the SAME role at the SAME entity whose last term ended before 2016-01-01 (years before any model's training cutoff),
choosing the most recent such holder. The question uses the same role phrase and template as the paired NEW-post item, so
entity, popularity, relation and template are held fixed; only the truth (and recency) of the presupposition differs.
Writes data/items_ancient.jsonl (ids ANC-####) and logs exclusions."""
import json, os, re, collections
R = os.path.join(os.path.dirname(__file__), "..")
CUT = "2016-01-01"
items = [json.loads(l) for l in open(os.path.join(R, "data", "items.jsonl"))]
new_post = [i for i in items if i["cond"] == "NEW" and i["t_change"] >= "2025-01-01"]
raw = {}
for rel in ("P6", "P35", "P169", "P286", "P488"):
    for b in json.load(open(os.path.join(R, "data", "raw", f"{rel}.json")))["results"]["bindings"]:
        y = b["y"]["value"].rsplit("/", 1)[1]; h = b["h"]["value"].rsplit("/", 1)[1]
        raw.setdefault((rel, y), []).append(dict(h=h, label=b.get("hLabel", {}).get("value", ""),
                                                 start=b.get("start", {}).get("value", "")[:10], end=b.get("end", {}).get("value", "")[:10]))
def surname(s): return s.split()[-1].lower() if s else ""
out, log = [], collections.Counter()
for k, it in enumerate(new_post):
    st = raw.get((it["rel"], it["y"]), [])
    by_h = collections.defaultdict(list)
    for s in st: by_h[s["h"]].append(s)
    cands = []
    for h, ss in by_h.items():
        if h == it["x"]: continue
        ends = [s["end"] for s in ss]
        if any(e == "" for e in ends): continue                 # an open-ended term: may still hold the role
        last = max(ends)
        if last >= CUT: continue                                  # must have left long before any cutoff
        lab = ss[0]["label"]
        if not lab or re.match(r"^Q\d+$", lab) or len(lab) > 60: continue
        if surname(lab) in (surname(it["x_l"]), surname(it.get("old_l", ""))): continue   # avoid same-surname confusions
        cands.append((last, h, lab))
    if not cands:
        log["no_candidate"] += 1; continue
    last, h, lab = max(cands)
    out.append(dict(id=f"ANC-{k:04d}", cond="STALE_ANCIENT", pair=it["id"], rel=it["rel"], y=it["y"], y_l=it["y_l"], y_sl=it["y_sl"],
                    role_full=it["role_full"], x=h, x_l=lab, truth=False, t_change=last, template=it["template"],
                    evidence_fresh=it["evidence_fresh"], evidence_stale=it["evidence_stale"]))
    log["ok"] += 1
with open(os.path.join(R, "data", "items_ancient.jsonl"), "w") as f:
    for o in out: f.write(json.dumps(o, ensure_ascii=False) + "\n")
json.dump(dict(log), open(os.path.join(R, "data", "items_ancient_log.json"), "w"))
print(dict(log)); [print(o["x_l"], "|", o["role_full"], "| left", o["t_change"]) for o in out[:12]]
