#!/bin/bash
# Round-1 additions (2026-11-17): template sweep for the identified-cutoff models; second judge (Mistral) on ALL generations.
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
for m in qwen2.5-3b qwen2.5-7b mistral-7b phi3.5-mini; do
  .venv/bin/python -u code/run_generate.py $m --sweep 2>&1 | $F
done
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/qwen2.5-3b_sweep.jsonl results/gen/qwen2.5-7b_sweep.jsonl results/gen/mistral-7b_sweep.jsonl results/gen/phi3.5-mini_sweep.jsonl 2>&1 | $F
echo SWEEPS4_DONE
.venv/bin/python -u code/judge.py mistral-7b results/gen/*.jsonl 2>&1 | $F
echo PIPELINE4_DONE
