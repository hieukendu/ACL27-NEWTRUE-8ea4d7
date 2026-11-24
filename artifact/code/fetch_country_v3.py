"""Round-3 (plausibility of the SWAP control): citizenship (P27) of every NEW/SWAP person in the entity triples (each SWAP
person is the new holder of another triple entity) and country (P17) of every triple entity, from the Wikidata API
(wbgetclaims, one call per entity, 3 s apart, honouring HTTP 429 Retry-After; resumable cache).
-> data/raw/wd_country_v3.json  {qid: [country qids]}. Used by analyze_v3_r3.py to split the triples into
nationality-compatible SWAP premises (the swapped person shares a citizenship with the true new holder or with the
entity's country) and the rest."""
import json, os, time, urllib.request, urllib.parse, urllib.error
R = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(R, "data", "raw", "wd_country_v3.json")
items = [json.loads(l) for l in open(os.path.join(R, "data", "items_v3.jsonl"))]
jobs = sorted({(i["x"], "P27") for i in items if i["cond"] in ("P3_NEW", "P3_SWAP")} | {(i["y"], "P17") for i in items})
out = json.load(open(OUT)) if os.path.exists(OUT) else {}
for x, p in jobs:
    if x in out: continue
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(dict(action="wbgetclaims", entity=x, property=p, format="json"))
    req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0 (academic use)"})
    for attempt in range(6):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=20)); break
        except urllib.error.HTTPError as e:
            time.sleep(int(e.headers.get("Retry-After", 30)) + 1)
        except Exception:
            time.sleep(10)
    else:
        print("giving up at", x); break
    vals = []
    for c in d.get("claims", {}).get(p, []):
        try: vals.append(c["mainsnak"]["datavalue"]["value"]["id"])
        except KeyError: pass
    out[x] = sorted(set(vals))
    json.dump(out, open(OUT, "w"), indent=0)
    time.sleep(3)
print(len(out), "of", len(jobs), "fetched;", sum(1 for v in out.values() if not v), "without a value")
