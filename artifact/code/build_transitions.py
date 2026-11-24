"""Turn raw Wikidata statements into (a) transitions old->new holder and (b) long-standing current holders.
Output: data/transitions.jsonl, data/oldtrue.jsonl  (snapshot = fetch date of raw files)."""
import json, os, re, time, collections, requests
D = os.path.join(os.path.dirname(__file__), "..", "data")
UA = "NewTrueResearchBot/0.1 (academic research)"
SNAP = "2026-11-10"
ROLE = {"P6": "head of government", "P35": "head of state", "P169": "CEO", "P286": "head coach", "P488": "chairperson", "P54": "player"}

def qid(u): return u.rsplit("/", 1)[-1]
def date(r, k): return r[k]["value"][:10] if k in r and not r[k]["value"].startswith("http") else None

def load(p):
    path = os.path.join(D, "raw", f"{p}.json")
    if not os.path.exists(path): return []
    rows = json.load(open(path))["results"]["bindings"]
    out = []
    for r in rows:
        if r["rank"]["value"].endswith("DeprecatedRank"): continue
        out.append(dict(rel=p, y=qid(r["y"]["value"]), yl=r["yLabel"]["value"], ys=int(r["ys"]["value"]),
                        h=qid(r["h"]["value"]), hl=r["hLabel"]["value"], hs=int(r["hs"]["value"]),
                        start=date(r, "start"), end=date(r, "end"),
                        office=r.get("officeLabel", {}).get("value")))
    return out

def fix_labels(stmts):
    need = {s["y"] for s in stmts if re.fullmatch(r"Q\d+", s["yl"])} | {s["h"] for s in stmts if re.fullmatch(r"Q\d+", s["hl"])}
    cache_p = os.path.join(D, "raw", "labels.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    todo = sorted(need - set(cache))
    for i in range(0, len(todo), 50):
        for attempt in range(5):
            try:
                r = requests.get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": "|".join(todo[i:i+50]),
                    "props": "labels", "languages": "en|mul", "format": "json", "maxlag": 5}, headers={"User-Agent": UA}, timeout=60).json()
                break
            except Exception as e:
                print("label retry", e); time.sleep(10 * (attempt + 1)); r = {}
        for q, e in r.get("entities", {}).items():
            lab = e.get("labels", {})
            cache[q] = (lab.get("en") or lab.get("mul") or {}).get("value")
        time.sleep(1)
    json.dump(cache, open(cache_p, "w"))
    for s in stmts:
        if s["y"] in cache and cache[s["y"]]: s["yl"] = cache[s["y"]]
        if s["h"] in cache and cache[s["h"]]: s["hl"] = cache[s["h"]]
    return [s for s in stmts if not re.fullmatch(r"Q\d+", s["yl"]) and not re.fullmatch(r"Q\d+", s["hl"])]

def days(a, b):
    import datetime as dt
    return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days

def valid(d): return d is not None and re.fullmatch(r"\d{4}-\d\d-\d\d", d) and "-00" not in d

def main():
    trans, oldtrue = [], []
    for p in ["P6", "P35", "P169", "P286", "P488", "P54"]:
        st = load(p)
        if not st: print("skip", p); continue
        st = [s for s in st if (s['start'] or '') >= '2015' or (s['end'] or '') >= '2015' or (s['end'] is None)]
        st = fix_labels(st)
        # P54: player-centric: key is the player (h); the 'slot' is the player's club
        key = (lambda s: s["h"]) if p == "P54" else (lambda s: s["y"])
        groups = collections.defaultdict(list)
        for s in st:
            if s["start"] and not valid(s["start"]): s["start"] = None
            if s["end"] and not valid(s["end"]): s["end"] = None
            groups[key(s)].append(s)
        nt = no = 0
        for k, ss in groups.items():
            other = (lambda s: s["y"]) if p == "P54" else (lambda s: s["h"])
            cur = [s for s in ss if s["end"] is None and s["start"]]
            if len({other(s) for s in cur}) != 1: continue        # ambiguous / no current holder
            # drop if the current partner also appears with an end date AFTER its start (re-appointment noise)
            c = max(cur, key=lambda s: s["start"])
            if c["start"] > SNAP: continue
            prev = [s for s in ss if s["end"] and other(s) != other(c) and abs(days(s["end"], c["start"])) <= 400]
            if prev:
                a = max(prev, key=lambda s: s["end"])
                if any(other(s) == other(c) and s["end"] and s["end"] > a["end"] for s in ss):
                    continue  # interleaved terms, skip
                if p == "P54":
                    rec = dict(rel=p, kind="player", holder=c["h"], holder_l=c["hl"], holder_sl=c["hs"],
                               new=c["y"], new_l=c["yl"], new_sl=c["ys"], old=a["y"], old_l=a["yl"], old_sl=a["ys"],
                               t_change=c["start"], old_end=a["end"], old_start=a["start"])
                else:
                    rec = dict(rel=p, kind="entity", ent=c["y"], ent_l=c["yl"], ent_sl=c["ys"], office=c["office"],
                               new=c["h"], new_l=c["hl"], new_sl=c["hs"], old=a["h"], old_l=a["hl"], old_sl=a["hs"],
                               t_change=c["start"], old_end=a["end"], old_start=a["start"])
                trans.append(rec); nt += 1
            if c["start"] <= "2021-12-31" and p != "P54":
                oldtrue.append(dict(rel=p, ent=c["y"], ent_l=c["yl"], ent_sl=c["ys"], office=c["office"],
                                    holder=c["h"], holder_l=c["hl"], holder_sl=c["hs"], t_start=c["start"],
                                    all_holders=sorted({s["h"] for s in ss})))
                no += 1
        print(p, "transitions", nt, "oldtrue", no)
    with open(os.path.join(D, "transitions.jsonl"), "w") as f:
        for r in trans: f.write(json.dumps(r) + "\n")
    with open(os.path.join(D, "oldtrue.jsonl"), "w") as f:
        for r in oldtrue: f.write(json.dumps(r) + "\n")
    # all holders per entity for never-true checks
    allh = collections.defaultdict(set)
    for p in ["P6", "P35", "P169", "P286", "P488"]:
        for s in load(p): allh[f"{p}|{s['y']}"].add(s["h"])
    json.dump({k: sorted(v) for k, v in allh.items()}, open(os.path.join(D, "all_holders.json"), "w"))

if __name__ == "__main__":
    main()
