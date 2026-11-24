#!/bin/bash
# Sequential (one model process at a time; shared GPU). Main grid, then template sweeps for small models.
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b qwen2.5-3b phi3.5-mini qwen2.5-7b mistral-7b; do
  .venv/bin/python -u code/run_generate.py $m 2>&1 | $F
done
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b qwen2.5-3b; do
  .venv/bin/python -u code/run_generate.py $m --sweep 2>&1 | $F
done
echo ALLGEN_DONE
