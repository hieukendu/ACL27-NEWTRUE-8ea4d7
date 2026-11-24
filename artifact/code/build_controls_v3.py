"""Round-2 rebuild of the false controls, all asked with template T2 ("What are the main priorities of x as the current r?"),
the only template whose presupposition is false for a former holder (T1 "since becoming r" and T3 "under x's leadership as r"
are historically true for one).

For every audited NEW-post entity (current holder N, became true >= 2025-01-01):
  P3N  true, newly true: N as the current r                                   (same entity, same template)
  P3A  false, familiar:  the most recent former holder A of the same role at the same entity whose last term ended before
                         2016-01-01, who is ALIVE (no Wikidata P570) and has no later term (round-2 fixes: Karamanlis->Papoulias,
                         deceased holders removed)
  P3S  false, unfamiliar: the NEW-post holder S of a DIFFERENT entity with the same relation (S became true >= 2025, so S is as
                         unknown to the models as N); derangement within relation, seed 0
Person popularity (Wikidata sitelinks of the person) is fetched for every presupposed person. Output: data/items_v3.jsonl and
data/items_v3_log.json. Requires network (Wikidata API); responses cached in data/raw/wd_persons.json."""
import json, os, re, random, collections, urllib.request, urllib.parse, urllib.error, time
R = os.path.join(os.path.dirname(__file__), "..")
CUT = "2016-01-01"
EXCL = json.load(open(os.path.join(R, "data", "exclusions.json")))
items = [json.loads(l) for l in open(os.path.join(R, "data", "items.jsonl"))]
newp = [i for i in items if i["cond"] == "NEW" and i["t_change"] >= "2025-01-01" and i["id"] not in EXCL]
raw = {}
for rel in ("P6", "P35", "P169", "P286", "P488"):
    for b in json.load(open(os.path.join(R, "data", "raw", f"{rel}.json")))["results"]["bindings"]:
        y = b["y"]["value"].rsplit("/", 1)[1]; h = b["h"]["value"].rsplit("/", 1)[1]
        raw.setdefault((rel, y), []).append(dict(h=h, label=b.get("hLabel", {}).get("value", ""),
                                                 start=b.get("start", {}).get("value", "")[:10], end=b.get("end", {}).get("value", "")[:10]))
cache_f = os.path.join(R, "data", "raw", "wd_persons.json")
cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
def wd(qids):
    need = sorted({q for q in qids if q not in cache})
    for k in range(0, len(need), 25):
        q = urllib.parse.urlencode(dict(action="wbgetentities", ids="|".join(need[k:k + 25]), props="claims|sitelinks", format="json"))
        req = urllib.request.Request(f"https://www.wikidata.org/w/api.php?{q}", headers={"User-Agent": "research-script/0.1 (academic, low volume)"})
        for attempt in range(8):
            try:
                ents = json.load(urllib.request.urlopen(req, timeout=30))["entities"]; break
            except urllib.error.HTTPError as e:
                if e.code != 429: raise
                time.sleep(int(e.headers.get("Retry-After", "30") or 30) + 5 * attempt)
        else:
            raise SystemExit("Wikidata rate limit: retry later")
        for qid, e in ents.items():
            cache[qid] = dict(dead=bool(e.get("claims", {}).get("P570")), sitelinks=len(e.get("sitelinks", {})))
        time.sleep(3)
    json.dump(cache, open(cache_f, "w"))
surname = lambda s: s.split()[-1].lower() if s else ""
# candidate former holders per entity
cand = {}
for it in newp:
    by_h = collections.defaultdict(list)
    for s in raw.get((it["rel"], it["y"]), []): by_h[s["h"]].append(s)
    cs = []
    for h, ss in by_h.items():
        if h == it["x"]: continue
        if any(s["start"] >= CUT for s in ss if s["start"]): continue           # held the role again after 2015
        ends = [s["end"] for s in ss if s["end"]]
        if not ends: continue
        last = max(ends)
        if last >= CUT: continue
        lab = ss[0]["label"]
        if not lab or re.match(r"^Q\d+$", lab) or len(lab) > 60: continue
        if surname(lab) in (surname(it["x_l"]), surname(it.get("old_l", ""))): continue
        cs.append((last, h, lab))
    cand[it["id"]] = sorted(cs, reverse=True)
wd([h for cs in cand.values() for _, h, _ in cs] + [it["x"] for it in newp])
out, log = [], collections.Counter()
for k, it in enumerate(newp):
    alive = [(last, h, lab) for last, h, lab in cand[it["id"]] if not cache.get(h, {}).get("dead")]
    if not alive: log["no_alive_former_holder"] += 1; continue
    last, h, lab = alive[0]
    base = dict(rel=it["rel"], y=it["y"], y_l=it["y_l"], y_sl=it["y_sl"], role_full=it["role_full"], template="T2",
                evidence_fresh=it["evidence_fresh"], evidence_stale=it["evidence_stale"], pair=it["id"])
    out.append(dict(base, id=f"P3N-{k:04d}", cond="P3_NEW", x=it["x"], x_l=it["x_l"], x_sl_wd=cache.get(it["x"], {}).get("sitelinks"), truth=True, t_change=it["t_change"]))
    out.append(dict(base, id=f"P3A-{k:04d}", cond="P3_ANC", x=h, x_l=lab, x_sl_wd=cache.get(h, {}).get("sitelinks"), truth=False, t_change=last))
    log["pairs"] += 1
# unfamiliar-but-false: derangement of NEW-post holders within relation (all audited NEW-post entities as donors)
rng = random.Random(0)
by_rel = collections.defaultdict(list)
for it in newp: by_rel[it["rel"]].append(it)
paired = {o["pair"] for o in out}
for rel, its in by_rel.items():
    if len(its) < 2: continue
    for _ in range(100):
        perm = its[:]; rng.shuffle(perm)
        if all(a["y"] != b["y"] and surname(a["x_l"]) != surname(b["x_l"]) for a, b in zip(its, perm)): break
    for a, b in zip(its, perm):
        if a["id"] not in paired: continue
        k = [o for o in out if o["pair"] == a["id"]][0]["id"].split("-")[1]
        out.append(dict(rel=rel, y=a["y"], y_l=a["y_l"], y_sl=a["y_sl"], role_full=a["role_full"], template="T2",
                        evidence_fresh=a["evidence_fresh"], evidence_stale=a["evidence_stale"], pair=a["id"],
                        id=f"P3S-{k}", cond="P3_SWAP", x=b["x"], x_l=b["x_l"], x_sl_wd=cache.get(b["x"], {}).get("sitelinks"),
                        truth=False, t_change=b["t_change"], swap_from=b["y_l"]))
        log["swaps"] += 1
with open(os.path.join(R, "data", "items_v3.jsonl"), "w") as f:
    for o in out: f.write(json.dumps(o, ensure_ascii=False) + "\n")
json.dump(dict(log), open(os.path.join(R, "data", "items_v3_log.json"), "w"))
print(dict(log))
for o in out[:9]: print(o["cond"], "|", o["x_l"], "|", o["role_full"], "|", o.get("x_sl_wd"))
