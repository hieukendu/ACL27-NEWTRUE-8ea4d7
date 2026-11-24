"""Stratified random subset (seed 0) of generations for the second judge: up to 40 per (model, condition, item-condition)."""
import json, glob, os, random, collections
R = os.path.join(os.path.dirname(__file__), "..")
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
rng = random.Random(0); groups = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(R, "results", "gen", "*.jsonl"))):
    if "_sweep" in f: continue
    for l in open(f):
        r = json.loads(l)
        if r["id"] not in items: continue
        groups[(r["model"], r["icond"], items[r["id"]]["cond"])].append((r["model"], r["id"], r["icond"], r["template"]))
sub = []
for k in sorted(groups):
    g = groups[k]; rng.shuffle(g); sub += g[:12]
json.dump(sub, open(os.path.join(R, "results", "labels", "subset.json"), "w"))
print("subset", len(sub))
