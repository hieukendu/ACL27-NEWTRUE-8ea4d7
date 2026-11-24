import json, sys, collections, glob, os
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","")
items={i["id"]:i for i in map(json.loads,open(B+"data/items.jsonl"))}
def g(i):
    if i["cond"]=="NEW": return "NEWp" if i["t_change"]>="2025-01-01" else "NEWn"
    return i["cond"]
for f in sorted(glob.glob(B+"results/labels/qwen2.5-7b/*.jsonl")):
  c=collections.defaultdict(collections.Counter)
  for l in open(f):
    r=json.loads(l)
    if r["id"] not in items or r["template"]!=items[r["id"]]["template"]: continue
    c[(r["icond"], g(items[r["id"]]))][r["label"]]+=1
  print(os.path.basename(f), "rebut/cv")
  for ic in ["plain","premise","date","rag_fresh","rag_stale","policy","policy_nodate"]:
    print(ic.ljust(13), "  ".join(f"{gg}:{c[(ic,gg)]['rebut']/max(1,sum(c[(ic,gg)].values())):.2f}/{c[(ic,gg)]['cannot_verify']/max(1,sum(c[(ic,gg)].values())):.2f}" for gg in ["NEWp","NEWn","OLD","STALE_POST","STALE_PRE","NEVER"]))
