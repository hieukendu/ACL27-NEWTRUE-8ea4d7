"""Automatic validation of candidate items against two independent signals (cached):
(1) office-label consistency: for P6/P35 items whose role phrase is an office label, the holder of the TRUE
    state must have a 'position held' (P39) statement for that office; otherwise use the generic role phrase.
(2) English Wikipedia lead-section check: the current (true) holder's surname must occur in section 0 (lead +
    infobox) of the entity's enwiki article. Items failing (2) are dropped (truth label not corroborated).
Writes data/items.jsonl (final frozen set) and data/validation_log.json."""
import json, os, re, time, requests, collections, sys
sys.path.insert(0, os.path.dirname(__file__))
D = os.path.join(os.path.dirname(__file__), "..", "data")
UA = "NewTrueResearchBot/0.1 (academic research, low volume; contact: anonymous-acl-submission)"
ROLE = {"P6": "head of government", "P35": "head of state", "P169": "CEO", "P286": "head coach", "P488": "chairperson"}
I = [json.loads(l) for l in open(os.path.join(D, "items_candidates.jsonl"))]
cache_p = os.path.join(D, "raw", "validation_cache.json")
C = json.load(open(cache_p)) if os.path.exists(cache_p) else {"p39": {}, "enwiki": {}, "lead": {}, "office_q": {}}

def get(url, params):
    for a in range(5):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30)
            if r.status_code == 200: return r.json()
        except Exception as e: print("retry", e)
        time.sleep(5 * (a + 1))
    return {}

# --- (1) office ids for entities and P39 of holders
def sparql(q):
    for a in range(6):
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": q, "format": "json"}, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"}, timeout=90)
            if r.status_code == 200: return r.json()["results"]["bindings"]
            print("sparql", r.status_code)
        except Exception as e: print("sparql retry", e)
        time.sleep(30 * (a + 1))
    raise SystemExit("sparql failed")
if not C["office_q"]:
    pairs = sorted({(i["y"], i["x"], i["rel"]) for i in I if i["rel"] in ("P6", "P35")})
    vals = " ".join(f"(wd:{y} wd:{x} wdt:{'P1313' if r == 'P6' else 'P1906'})" for y, x, r in pairs)
    rows = sparql("SELECT ?y ?x ?office ?held WHERE { VALUES (?y ?x ?op) { " + vals + " } ?y ?op ?office . "
                  "BIND(EXISTS { ?x p:P39/ps:P39 ?office } AS ?held) }")
    for r in rows:
        y = r["y"]["value"].rsplit("/", 1)[-1]; x = r["x"]["value"].rsplit("/", 1)[-1]; o = r["office"]["value"].rsplit("/", 1)[-1]
        C["office_q"].setdefault(y, {"P1313": [], "P1906": []})
        for k in ("P1313", "P1906"):
            if o not in C["office_q"][y][k]: C["office_q"][y][k].append(o)
        if r["held"]["value"] == "true": C["p39"].setdefault(x, []).append(o)
    C["office_q"]["_done"] = True
curmap = {}
for i in I:
    m = re.match(r"(.+?) (has been|is) ", i["evidence_fresh"]); curmap[i["id"]] = m.group(1)
json.dump(C, open(cache_p, "w"))

log = collections.Counter()
for i in I:
    if i["rel"] in ("P6", "P35") and not i["role_full"].startswith(ROLE[i["rel"]]):
        offs = C["office_q"].get(i["y"], {}).get("P1313" if i["rel"] == "P6" else "P1906", [])
        # the role phrase must be valid for the person presupposed when true, and for the old holder when stale
        ok = any(o in C["p39"].get(i["x"], []) for o in offs) if i["cond"] != "NEVER" else True
        if not ok:
            generic = f"{ROLE[i['rel']]} of {i['y_l']}"
            for k in ("evidence_fresh", "evidence_stale"):
                i[k] = i[k].replace(i["role_full"], generic)
            i["role_full"] = generic; log["office_label_replaced"] += 1
# NEVER items must use the same role phrase validity; a NEVER item with an office label is fine (false anyway)

# --- (2) enwiki lead-section check
need = [q for q in sorted({i["y"] for i in I}) if q not in C["enwiki"]]
if need:
    rows = sparql("SELECT ?y ?t WHERE { VALUES ?y { " + " ".join("wd:" + q for q in need) + " } OPTIONAL { ?a schema:about ?y ; schema:isPartOf <https://en.wikipedia.org/> ; schema:name ?t } }")
    for q in need: C["enwiki"][q] = None
    for r in rows:
        if "t" in r: C["enwiki"][r["y"]["value"].rsplit("/", 1)[-1]] = r["t"]["value"]
json.dump(C, open(cache_p, "w"))
titles = sorted({t for t in C["enwiki"].values() if t} - set(C["lead"]))
for n in range(0, len(titles), 10):
    batch = titles[n:n + 10]
    r = get("https://en.wikipedia.org/w/api.php", {"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "titles": "|".join(batch), "redirects": 1, "format": "json", "formatversion": 2})
    norm_map = {x["from"]: x["to"] for x in r.get("query", {}).get("normalized", []) + r.get("query", {}).get("redirects", [])}
    pages = {pg["title"]: pg for pg in r.get("query", {}).get("pages", [])}
    for t in batch:
        tt = norm_map.get(norm_map.get(t, t), norm_map.get(t, t))
        pg = pages.get(tt, {})
        txt = pg.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "") if pg.get("revisions") else ""
        # section 0 = text before the first level-2 heading (lead + infobox)
        m = re.search(r"\n==[^=]", txt)
        C["lead"][t] = txt[:m.start()] if m else txt[:20000]
    time.sleep(1)
    json.dump(C, open(cache_p, "w")); print("lead", n, len(titles))
json.dump(C, open(cache_p, "w"))

def surname(name):
    name = re.sub(r"\(.*?\)", "", name).replace("Sir ", "").strip()
    toks = [t for t in re.split(r"[\s]+", name) if t and not re.fullmatch(r"[IVX]+|Jr\.?|Sr\.?", t)]
    return toks[-1] if toks else name

def norm(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()

final = []
for i in I:
    cur = curmap[i["id"]]
    title = C["enwiki"].get(i["y"])
    lead = norm(C["lead"].get(title, "") if title else "")
    i["enwiki"] = title
    i["wiki_current_holder_in_lead"] = bool(lead) and norm(surname(cur)) in lead
    if not title: log["no_enwiki"] += 1
    if i["wiki_current_holder_in_lead"]:
        final.append(i); log[f"keep_{i['cond']}"] += 1
    else:
        log[f"drop_{i['cond']}"] += 1
with open(os.path.join(D, "items.jsonl"), "w") as f:
    for i in final: f.write(json.dumps(i) + "\n")
json.dump(dict(log), open(os.path.join(D, "validation_log.json"), "w"), indent=1)
print(dict(log)); print("final", len(final), collections.Counter(i["cond"] for i in final))
