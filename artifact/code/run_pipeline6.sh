#!/bin/bash
# Round-1 revision: entity-matched ancient-holder control (data/items_ancient.jsonl), identified-cutoff models, 7 conditions.
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
for m in qwen2.5-3b qwen2.5-7b mistral-7b phi3.5-mini; do
  .venv/bin/python -u code/run_generate.py $m --items data/items_ancient.jsonl 2>&1 | $F
done
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/*_anc.jsonl 2>&1 | $F
.venv/bin/python -u code/judge.py mistral-7b results/gen/*_anc.jsonl 2>&1 | $F
echo PIPELINE6_DONE
