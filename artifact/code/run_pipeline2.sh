#!/bin/bash
# Second half of the GPU queue (reordered so that labels for the main grid are available first).
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
MAIN="results/gen/qwen2.5-0.5b.jsonl results/gen/qwen2.5-1.5b.jsonl results/gen/smollm2-1.7b.jsonl results/gen/qwen2.5-3b.jsonl results/gen/phi3.5-mini.jsonl results/gen/qwen2.5-7b.jsonl results/gen/mistral-7b.jsonl"
.venv/bin/python -u code/judge.py qwen2.5-7b $MAIN 2>&1 | $F
echo JUDGE_MAIN_DONE
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b; do
  .venv/bin/python -u code/run_generate.py $m --sweep 2>&1 | $F
done
.venv/bin/python -u code/run_generate.py qwen3.5-4b --conds plain,premise,policy 2>&1 | $F
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/*_sweep.jsonl results/gen/qwen3.5-4b.jsonl 2>&1 | $F
.venv/bin/python -u code/make_judge_subset.py
.venv/bin/python -u code/judge.py mistral-7b results/gen/*.jsonl --subset results/labels/subset.json 2>&1 | $F
echo PIPELINE2_DONE
