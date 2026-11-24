"""Fetch time-qualified office/role statements from Wikidata (cached in data/raw/).
Polite: one query at a time, custom UA, sleeps between queries, results cached."""
import json, os, sys, time, requests
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
UA = "NewTrueResearchBot/0.1 (academic research; contact: anonymous-acl-submission)"
EP = "https://query.wikidata.org/sparql"

# relation -> (property, min sitelinks of subject entity, extra filter)
RELS = {
    "P6":   ("P6", 15, ""),     # head of government
    "P35":  ("P35", 15, ""),    # head of state
    "P169": ("P169", 8, ""),    # CEO
    "P286": ("P286", 8, ""),    # head coach
    "P488": ("P488", 8, ""),    # chairperson
}
Q_SUBJ = """
SELECT ?y ?yLabel ?ys ?h ?hLabel ?hs ?start ?end ?rank ?office ?officeLabel WHERE {{
  ?y p:{p} ?st . ?st ps:{p} ?h ; wikibase:rank ?rank .
  ?y wikibase:sitelinks ?ys . FILTER(?ys >= {minsl})
  ?h wikibase:sitelinks ?hs .
  OPTIONAL {{ ?st pq:P580 ?start }}
  OPTIONAL {{ ?st pq:P582 ?end }}
  FILTER(BOUND(?start) || BOUND(?end))
  OPTIONAL {{ ?y {officeprop} ?office }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}"""
OFFICEPROP = {"P6": "wdt:P1313", "P35": "wdt:P1906"}

# P54 member of sports team: statements live on the player
Q_P54 = """
SELECT ?h ?hLabel ?hs ?y ?yLabel ?ys ?start ?end ?rank WHERE {
  ?h wdt:P106 wd:Q937857 ; wikibase:sitelinks ?hs . FILTER(?hs >= 45)
  ?h p:P54 ?st . ?st ps:P54 ?y ; wikibase:rank ?rank .
  ?y wikibase:sitelinks ?ys . FILTER(?ys >= 20)
  OPTIONAL { ?st pq:P580 ?start }
  OPTIONAL { ?st pq:P582 ?end }
  FILTER(BOUND(?start))
  FILTER NOT EXISTS { ?y wdt:P31 wd:Q6979593 }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""

def run(q, name):
    path = os.path.join(OUT, f"{name}.json")
    if os.path.exists(path):
        print("cached", name); return
    for attempt in range(4):
        r = requests.get(EP, params={"query": q, "format": "json"}, headers={"User-Agent": UA}, timeout=300)
        if r.status_code == 200:
            data = r.json()
            data["_fetched_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            json.dump(data, open(path, "w"))
            print(name, len(data["results"]["bindings"]), "rows"); return
        print(name, "status", r.status_code, r.text[:200]); time.sleep(30 * (attempt + 1))
    sys.exit(f"failed {name}")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, (p, msl, _) in RELS.items():
        q = Q_SUBJ.format(p=p, minsl=msl, officeprop=OFFICEPROP.get(p, "wdt:P1313"))
        if p not in OFFICEPROP:
            q = q.replace("OPTIONAL { ?y wdt:P1313 ?office }", "")
        run(q, name); time.sleep(5)
    # P54 (member of sports team) was attempted but the query times out on WDQS (60 s limit); not used.
