"""Round-1 judge validation: silver labels from a stronger model (Claude Sonnet 5.5, Anthropic API) on a stratified random
sample of main-grid responses, using the same judge prompt as every other judge (code/judge.py). Silver labels are NOT human
labels; they estimate how far each 7B / small judge departs from a stronger annotator.
Sample (seed 0): identified-cutoff models x {plain, premise, rag_fresh, rag_stale, policy} x {NEW_post, OLD, STALE_PRE, NEVER,
STALE_ANCIENT if available}, up to 8 per cell. Writes results/labels/silver-claude-sonnet-5-5/silver.jsonl (resumable)."""
import os, sys, json, re, glob, random
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(__file__))
from judge import JUDGE_SYS, JUDGE_TMPL
from judge_api import client
from prompts import question
R = os.path.join(os.path.dirname(__file__), "..")
MODEL = "claude-sonnet-5-5"; PER = 8
LAB = {"A": "accept", "B": "rebut", "C": "cannot_verify", "D": "refuse"}
items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
anc = os.path.join(R, "data", "items_ancient.jsonl")
if os.path.exists(anc): items.update({i["id"]: i for i in map(json.loads, open(anc))})
for extra in ("items_pairs_t2.jsonl", "items_v3.jsonl"):
    fx = os.path.join(R, "data", extra)
    if os.path.exists(fx): items.update({i["id"]: i for i in map(json.loads, open(fx))})
t2 = os.path.join(R, "data", "items_pairs_t2.jsonl")
if os.path.exists(t2): items.update({i["id"]: i for i in map(json.loads, open(t2))})
def group(i):
    if i["cond"] == "NEW": return "NEW_post" if i["t_change"] >= "2025-01-01" else "NEW_near"
    return i["cond"]
ID = json.load(open(os.path.join(R, "results", "analysis", "main.json")))["id_models"]
gens = {}
for f in glob.glob(os.path.join(R, "results", "gen", "*.jsonl")):
    if any(s in f for s in ("_sweep", "_long")): continue
    for l in open(f):
        r = json.loads(l)
        if r["id"] in items and r["template"] == items[r["id"]]["template"]: gens[(r["model"], r["id"], r["icond"], r["template"])] = r["response"]
cells = {}
for k in sorted(gens):
    m, i, c, t = k
    if m in ID and c in ("plain", "premise", "rag_fresh", "rag_stale", "policy") and group(items[i]) in ("NEW_post", "OLD", "STALE_PRE", "NEVER", "STALE_ANCIENT"):
        cells.setdefault((m, c, group(items[i])), []).append(k)
rng = random.Random(0); sample = []
for key in sorted(cells):
    ks = cells[key][:]; rng.shuffle(ks); sample += ks[:PER]
KEYS_FILE = sys.argv[sys.argv.index("--keys") + 1] if "--keys" in sys.argv else None
NOREASON = "--noreason" in sys.argv
# round-3: --retry re-asks, with a short reasoning budget ending in "Label: X", the held-out keys whose letter-only reply
# did not parse (Sonnet sometimes starts a sentence instead of a letter, and the 8-token cap cuts it off)
if "--retry" in sys.argv: NOREASON = False
if KEYS_FILE:   # round-2 held-out set (triples): label exactly these keys, letter-only (no reasoning) to limit cost
    for f in glob.glob(os.path.join(R, "results", "gen", "*_v3.jsonl")):
        for l in open(f):
            r = json.loads(l); gens[(r["model"], r["id"], r["icond"], r["template"])] = r["response"]
    sample = [tuple(k) for k in json.load(open(KEYS_FILE)) if tuple(k) in gens]
od = os.path.join(R, "results", "labels", "silver-claude-sonnet-5-5"); os.makedirs(od, exist_ok=True)
out = os.path.join(od, "silver_v3.jsonl" if KEYS_FILE else "silver.jsonl")
done = {tuple(json.loads(l)["key"]) for l in open(out)} if os.path.exists(out) else set()
todo = [k for k in sample if tuple(k) not in done]
print("sample", len(sample), "todo", len(todo), flush=True)
cl = client(); use = [0, 0]
def one(k):
    it = items[k[1]]
    u = JUDGE_TMPL.format(q=question(it, k[3]), x=it["x_l"], role=it["role_full"], resp=gens[k][:1200])
    if NOREASON:
        r = cl.messages.create(model=MODEL, max_tokens=8, system=JUDGE_SYS, thinking={"type": "between_tools"},
                               output_config={"effort": "low"}, messages=[{"role": "user", "content": u}])
    else:
        r = cl.messages.create(model=MODEL, max_tokens=400, system=JUDGE_SYS + "\nThink carefully, then end your reply with 'Label: <letter>'.",
                               output_config={"effort": "low"}, messages=[{"role": "user", "content": u}])
    t = "".join(b.text for b in r.content if b.type == "text")
    use[0] += r.usage.input_tokens; use[1] += r.usage.output_tokens
    m_ = re.findall(r"Label:\s*\(?([ABCD])", t) or re.findall(r"^\(?([ABCD])\)?(?:[\s.):,]|$)", t.strip()) or re.findall(r"\b([ABCD])\b", t[-20:])
    return k, (LAB[m_[-1]] if m_ else None), t
unparsed = []   # round-3: replies without a parseable letter are logged (they were silently dropped before)
with ThreadPoolExecutor(8) as ex, open(out, "a") as f:
    for k, lab, raw in ex.map(one, todo):
        if lab: f.write(json.dumps(dict(key=list(k), label=lab)) + "\n")
        else: unparsed.append(dict(key=list(k), raw=raw[:80]))
if unparsed:
    with open(os.path.join(od, "unparsed.jsonl"), "a") as f:
        for u in unparsed: f.write(json.dumps(u) + "\n")
cost = use[0] / 1e6 * 2.0 + use[1] / 1e6 * 10.0
with open(os.path.join(od, "usage.log"), "a") as f:
    f.write(json.dumps(dict(n=len(todo), unparsed=len(unparsed), keys=os.path.basename(KEYS_FILE) if KEYS_FILE else None, input=use[0], output=use[1], cost_usd=round(cost, 3))) + "\n")
print("done", len(todo), f"cost {cost:.2f}")
