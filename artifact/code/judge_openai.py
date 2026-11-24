"""Cross-family judge (round 2): OpenAI gpt-5.3-codex labels responses with the SAME judge prompt as every other judge
(code/judge.py), so that judge validation no longer rests on one model family (reviewer R1, round 2).
usage: judge_openai.py GEN_FILE [GEN_FILE ...] [--keys FILE.json] [--limit N] [--model ID]
  --keys: a JSON list of [model, id, icond, template] keys to label (e.g. the held-out silver sample); default: all rows.
-> results/labels/openai-<model>/<genfile basename> (resumable); token usage in usage.log.
The API key is read from $OPENAI_API_KEY, or from the file named by $OPENAI_KEY_FILE, and never printed."""
import sys, os, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
sys.path.insert(0, os.path.dirname(__file__))
from judge import JUDGE_SYS, JUDGE_TMPL
from prompts import question
R = os.path.join(os.path.dirname(__file__), "..")
LAB = {"A": "accept", "B": "rebut", "C": "cannot_verify", "D": "refuse"}

def parse(txt):
    t = (txt or "").strip()
    m = re.match(r"^\(?([ABCD])\)?(?:[\s.):,]|$)", t)
    if m: return LAB[m.group(1)]
    m = re.search(r"(?:label|answer)\s*(?:is)?\s*[:\-]?\s*\(?([ABCD])\b", t, re.I)
    return LAB[m.group(1).upper()] if m else None

def client():
    k = os.environ.get("OPENAI_API_KEY")
    if not k:
        kf = os.environ.get("OPENAI_KEY_FILE")
        if not kf: sys.exit("set OPENAI_API_KEY or OPENAI_KEY_FILE")
        k = re.search(r"sk-[A-Za-z0-9_\-]+", open(kf).read()).group(0)
    return openai.OpenAI(api_key=k, max_retries=6)

def load_items():
    items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
    for extra in ("items_ancient.jsonl", "items_pairs_t2.jsonl", "items_v3.jsonl"):
        fx = os.path.join(R, "data", extra)
        if os.path.exists(fx): items.update({i["id"]: i for i in map(json.loads, open(fx))})
    return items

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = lambda name: sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None
    for o in ("--keys", "--limit", "--model"):
        if opt(o): args.remove(opt(o))
    model = opt("--model") or "gpt-5.3-codex"
    keyset = set(tuple(k) for k in json.load(open(opt("--keys")))) if opt("--keys") else None
    limit = int(opt("--limit")) if opt("--limit") else None
    items = load_items(); cl = client(); lock = threading.Lock()
    od = os.path.join(R, "results", "labels", f"openai-{model}"); os.makedirs(od, exist_ok=True)
    use = dict(input=0, output=0, reasoning=0, n=0, unparsed=0)
    for gf in args:
        out = os.path.join(od, os.path.basename(gf))
        done = set()
        if os.path.exists(out):
            for l in open(out):
                r = json.loads(l); done.add((r["model"], r["id"], r["icond"], r["template"]))
        rows = [json.loads(l) for l in open(gf)]
        rows = [r for r in rows if r["id"] in items and (r["model"], r["id"], r["icond"], r["template"]) not in done
                and (keyset is None or (r["model"], r["id"], r["icond"], r["template"]) in keyset)]
        if limit: rows = rows[:limit]
        print(model, os.path.basename(gf), len(rows), flush=True)
        if not rows: continue
        def one(r):
            it = items[r["id"]]
            u = JUDGE_TMPL.format(q=question(it, r["template"]), x=it["x_l"], role=it["role_full"], resp=r["response"][:1200])
            resp = cl.responses.create(model=model, instructions=JUDGE_SYS, input=u, reasoning={"effort": "low"}, max_output_tokens=400)
            return r, resp.output_text, resp.usage
        with open(out, "a") as f, ThreadPoolExecutor(8) as ex:
            futs = [ex.submit(one, r) for r in rows]
            for fu in as_completed(futs):
                try:
                    r, txt, us = fu.result()
                except openai.APIStatusError as e:
                    print("API error", e.status_code, flush=True); continue
                except openai.APIConnectionError:
                    print("connection error", flush=True); continue
                lab = parse(txt)
                with lock:
                    use["n"] += 1; use["input"] += us.input_tokens; use["output"] += us.output_tokens
                    use["reasoning"] += getattr(getattr(us, "output_tokens_details", None), "reasoning_tokens", 0) or 0
                    if lab is None: use["unparsed"] += 1; continue
                    f.write(json.dumps(dict(model=r["model"], id=r["id"], icond=r["icond"], template=r["template"], label=lab, raw=(txt or "")[:40])) + "\n")
    print("usage", json.dumps(use))
    with open(os.path.join(od, "usage.log"), "a") as f:
        f.write(json.dumps(dict(time=time.strftime("%Y-%m-%d %H:%M"), model=model, files=[os.path.basename(a) for a in args], **use)) + "\n")

if __name__ == "__main__":
    main()
