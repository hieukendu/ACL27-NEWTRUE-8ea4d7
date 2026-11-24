"""Greedy generation for every item x intervention. Resumable. Writes results/gen/<model>.jsonl
usage: run_generate.py MODEL [--sweep]   (--sweep: plain condition with all 3 templates)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
from lm import load, chat, generate
from prompts import build, CONDS, TEMPLATES
R = os.path.join(os.path.dirname(__file__), "..")
name = sys.argv[1]; sweep = "--sweep" in sys.argv
CONDS_RUN = sys.argv[sys.argv.index("--conds") + 1].split(",") if "--conds" in sys.argv else None
BS = {"qwen2.5-14b": 32, "qwen2.5-32b": 16, "phi4": 32, "mistral-small-24b": 24, "qwen2.5-0.5b": 64, "qwen2.5-1.5b": 64, "smollm2-1.7b": 64, "qwen2.5-3b": 48, "phi3.5-mini": 32, "qwen3.5-4b": 32, "qwen2.5-7b": 64, "mistral-7b": 64}.get(name, 32)
MAXNEW = int(sys.argv[sys.argv.index("--maxnew") + 1]) if "--maxnew" in sys.argv else 48
LONG = MAXNEW != 48   # long-generation check writes <model>_long.jsonl (Plain, NEW and STALE_PRE items only)
ITEMS_FILE = sys.argv[sys.argv.index("--items") + 1] if "--items" in sys.argv else os.path.join(R, "data", "items.jsonl")
ANC = "--items" in sys.argv   # round-1 addition: entity-matched ancient-holder control -> <model>_anc.jsonl
I = [json.loads(l) for l in open(ITEMS_FILE)]
os.makedirs(os.path.join(R, "results", "gen"), exist_ok=True)
out = os.path.join(R, "results", "gen", f"{name}{'_sweep' if sweep else ''}{'_long' if LONG else ''}{('_anc' if os.path.basename(ITEMS_FILE) == 'items_ancient.jsonl' else '_' + os.path.basename(ITEMS_FILE)[6:-6]) if ANC else ''}.jsonl")
done = set()
if os.path.exists(out):
    for l in open(out):
        r = json.loads(l); done.add((r["id"], r["icond"], r["template"]))
jobs = []
for it in I:
    if LONG:
        # round-3: the triples (P3_*) are included so the cap can be checked on the main test (-> <model>_long_v3.jsonl)
        if it["cond"] in ("NEW", "STALE_PRE", "OLD", "P3_NEW", "P3_ANC", "P3_SWAP"): jobs.append((it, "plain", it["template"]))
        continue
    if sweep:
        for tp in TEMPLATES:
            jobs.append((it, "plain", tp))
    else:
        for c in (CONDS_RUN or CONDS):
            jobs.append((it, c, it["template"]))
jobs = [j for j in jobs if (j[0]["id"], j[1], j[2]) not in done]
print(name, "jobs", len(jobs)); sys.stdout.flush()
if not jobs: sys.exit()
tok, model = load(name)
t0 = time.time()
CH = 512
for k in range(0, len(jobs), CH):
    chunk = jobs[k:k + CH]
    prompts = []
    for it, c, tp in chunk:
        s, u = build(it, c, tp); prompts.append(chat(tok, name, s, u))
    outs = generate(tok, model, prompts, MAXNEW, BS)
    with open(out, "a") as f:
        for (it, c, tp), o in zip(chunk, outs):
            f.write(json.dumps(dict(id=it["id"], icond=c, template=tp, model=name, response=o)) + "\n")
    print(name, k + len(chunk), "/", len(jobs), f"{time.time() - t0:.0f}s"); sys.stdout.flush()
