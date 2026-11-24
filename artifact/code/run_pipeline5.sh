#!/bin/bash
# Round-1 revision experiments (2026-11-17): extra baselines and a long-generation check, identified-cutoff models.
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
for m in qwen2.5-3b qwen2.5-7b mistral-7b phi3.5-mini; do
  .venv/bin/python -u code/run_generate.py $m --conds cutoff_date,rag_mixed 2>&1 | $F
  .venv/bin/python -u code/run_generate.py $m --maxnew 256 2>&1 | $F
done
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/qwen2.5-3b.jsonl results/gen/qwen2.5-7b.jsonl results/gen/mistral-7b.jsonl results/gen/phi3.5-mini.jsonl results/gen/*_long.jsonl 2>&1 | $F
.venv/bin/python -u code/judge.py mistral-7b results/gen/qwen2.5-3b.jsonl results/gen/qwen2.5-7b.jsonl results/gen/mistral-7b.jsonl results/gen/phi3.5-mini.jsonl results/gen/*_long.jsonl 2>&1 | $F
echo PIPELINE5_DONE
