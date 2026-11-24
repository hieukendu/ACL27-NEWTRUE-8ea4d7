#!/bin/bash
# Resumption of run_pipeline2.sh after the 2026-11-10 pause (same jobs, reordered: second judge first; Qwen3.5 last).
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
.venv/bin/python -u code/make_judge_subset.py
.venv/bin/python -u code/judge.py mistral-7b results/gen/*.jsonl --subset results/labels/subset.json 2>&1 | $F
echo SECOND_JUDGE_DONE
for m in qwen2.5-1.5b smollm2-1.7b; do
  .venv/bin/python -u code/run_generate.py $m --sweep 2>&1 | $F
done
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/*_sweep.jsonl 2>&1 | $F
echo SWEEPS_DONE
.venv/bin/python -u code/run_generate.py qwen3.5-4b --conds plain,premise,policy 2>&1 | $F
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/qwen3.5-4b.jsonl 2>&1 | $F
echo PIPELINE3_DONE
