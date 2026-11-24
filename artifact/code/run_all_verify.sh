#!/bin/bash
cd "$(dirname "$0")/.."
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b qwen2.5-3b phi3.5-mini qwen2.5-7b mistral-7b qwen3.5-4b; do
  .venv/bin/python -u code/run_verify.py $m 2>&1 | grep --line-buffered -v -i warn
done
