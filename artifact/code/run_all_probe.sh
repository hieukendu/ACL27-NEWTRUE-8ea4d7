#!/bin/bash
# runs one model at a time (shared GPU)
cd "$(dirname "$0")/.."
for m in qwen2.5-0.5b qwen2.5-1.5b qwen2.5-3b qwen2.5-7b mistral-7b phi3.5-mini smollm2-1.7b qwen3.5-4b; do
  .venv/bin/python code/run_probe.py $m 2>&1 | grep -v -i "warn\|Loading weights\|redirects"
done
