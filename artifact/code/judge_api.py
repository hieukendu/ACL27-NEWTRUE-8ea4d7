"""Third judge: Claude Haiku 5.5 via the Anthropic API (cheapest Claude model), same prompt and A/B/C/D scheme as judge.py.
usage: judge_api.py GEN_FILE [GEN_FILE ...] [--subset FILE] [--limit N]
  -> results/labels/claude-haiku-5-5/<genfile basename>  (resumable; also logs token usage)
The API key is read from $ANTHROPIC_API_KEY, or from the file named by $ANTHROPIC_KEY_FILE, and never printed."""
import sys, os, json, re, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import anthropic
sys.path.insert(0, os.path.dirname(__file__))
from judge import JUDGE_SYS, JUDGE_TMPL
from prompts import question
R = os.path.join(os.path.dirname(__file__), "..")
MODEL = "claude-haiku-5-5"
LAB = {"A": "accept", "B": "rebut", "C": "cannot_verify", "D": "refuse"}

def parse(txt):
    """Round-2 fix (reviewer R3): the old parser took the first A-D character anywhere in the reply, so 'The answer is B'
    became A. Accept only a reply that IS a letter (optionally with ')' or '.'), or an explicit 'Label/Answer: X'."""
    t = txt.strip()
    m = re.match(r"^\(?([ABCD])\)?(?:[\s.):,]|$)", t)
    if m: return LAB[m.group(1)]
    m = re.search(r"(?:label|answer)\s*(?:is)?\s*[:\-]?\s*\(?([ABCD])\b", t, re.I)
    return LAB[m.group(1).upper()] if m else None

def client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        kf = os.environ.get("ANTHROPIC_KEY_FILE")
        if not kf: sys.exit("set ANTHROPIC_API_KEY or ANTHROPIC_KEY_FILE")
        m = re.search(r"sk-ant-[A-Za-z0-9_\-]+", open(kf).read())
        if not m: sys.exit("no Anthropic key found in $ANTHROPIC_KEY_FILE")
        key = m.group(0)
    return anthropic.Anthropic(api_key=key, max_retries=6)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    subset = limit = None
    if "--subset" in sys.argv:
        sf = sys.argv[sys.argv.index("--subset") + 1]; args.remove(sf)
        subset = set(tuple(x) for x in json.load(open(sf)))
    if "--limit" in sys.argv:
        lv = sys.argv[sys.argv.index("--limit") + 1]; args.remove(lv); limit = int(lv)
    RELABEL = "--relabel_bad" in sys.argv
    items = {i["id"]: i for i in map(json.loads, open(os.path.join(R, "data", "items.jsonl")))}
    anc = os.path.join(R, "data", "items_ancient.jsonl")   # round-1 control items
    if os.path.exists(anc): items.update({i["id"]: i for i in map(json.loads, open(anc))})
    for extra in ("items_pairs_t2.jsonl", "items_v3.jsonl"):   # round-2 controls
        fx = os.path.join(R, "data", extra)
        if os.path.exists(fx): items.update({i["id"]: i for i in map(json.loads, open(fx))})
    cl = client(); lock = threading.Lock()
    od = os.path.join(R, "results", "labels", MODEL); os.makedirs(od, exist_ok=True)
    usage = dict(input=0, output=0, n=0, bad=0)
    for gf in args:
        out = os.path.join(od, os.path.basename(gf))
        done = set(); kept = []
        if os.path.exists(out):
            for l in open(out):
                r = json.loads(l)
                if RELABEL and parse(r.get("raw", "")) is None:   # drop labels parsed from free text; they are re-queried
                    continue
                done.add((r["model"], r["id"], r["icond"], r["template"])); kept.append(l)
            if RELABEL:
                open(out, "w").writelines(kept)
        rows = [json.loads(l) for l in open(gf)]
        rows = [r for r in rows if r["id"] in items and (r["model"], r["id"], r["icond"], r["template"]) not in done
                and (subset is None or (r["model"], r["id"], r["icond"], r["template"]) in subset)]
        if limit: rows = rows[:limit]
        print(MODEL, gf, len(rows), flush=True)
        if not rows: continue

        def one(r):
            it = items[r["id"]]
            u = JUDGE_TMPL.format(q=question(it, r["template"]), x=it["x_l"], role=it["role_full"], resp=r["response"][:1200])
            resp = cl.messages.create(model=MODEL, max_tokens=16, system=JUDGE_SYS,
                                      thinking={"type": "disabled"}, output_config={"effort": "low"},
                                      messages=[{"role": "user", "content": u}])
            txt = "".join(b.text for b in resp.content if b.type == "text").strip()
            lab = parse(txt)
            if lab is None:   # round-2 fix: never take a letter out of free text; re-ask for the letter only
                resp2 = cl.messages.create(model=MODEL, max_tokens=4, system=JUDGE_SYS, thinking={"type": "disabled"}, output_config={"effort": "low"},
                                           messages=[{"role": "user", "content": u}, {"role": "assistant", "content": txt or "(no answer)"},
                                                     {"role": "user", "content": "Reply with exactly one letter: A, B, C or D."}])
                txt = "".join(b.text for b in resp2.content if b.type == "text").strip()
                lab = parse(txt)
            return r, lab, txt, resp.usage

        t0 = time.time()
        with open(out, "a") as f, ThreadPoolExecutor(12) as ex:
            futs = [ex.submit(one, r) for r in rows]
            for k, fu in enumerate(as_completed(futs)):
                try:
                    r, lab, txt, us = fu.result()
                except anthropic.APIStatusError as e:
                    print("API error", e.status_code, flush=True); continue
                except anthropic.APIConnectionError:
                    print("connection error", flush=True); continue
                with lock:
                    usage["input"] += us.input_tokens; usage["output"] += us.output_tokens; usage["n"] += 1
                    if lab is None: usage["bad"] += 1; continue
                    f.write(json.dumps(dict(model=r["model"], id=r["id"], icond=r["icond"], template=r["template"],
                                            label=lab, raw=txt[:40])) + "\n")
                if (k + 1) % 250 == 0:
                    print(f"{k + 1}/{len(rows)} {time.time() - t0:.0f}s", flush=True)
    cost = usage["input"] / 1e6 * 0.10 + usage["output"] / 1e6 * 0.50
    print("usage", json.dumps(usage), f"cost_usd={cost:.3f}")
    with open(os.path.join(od, "usage.log"), "a") as f:
        f.write(json.dumps(dict(time=time.strftime("%Y-%m-%d %H:%M"), files=[os.path.basename(a) for a in args], **usage, cost_usd=round(cost, 4))) + "\n")

if __name__ == "__main__":
    main()
