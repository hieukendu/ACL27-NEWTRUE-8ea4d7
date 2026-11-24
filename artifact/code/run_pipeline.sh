#!/bin/bash
# Full GPU queue, strictly one model process at a time.
cd "$(dirname "$0")/.."
while pgrep -f run_all_probe.sh >/dev/null; do sleep 20; done
./code/run_all_verify.sh
./code/run_all_gen.sh
.venv/bin/python -u code/run_generate.py qwen3.5-4b --conds plain,premise,policy 2>&1 | grep --line-buffered -v -i warn
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/*.jsonl 2>&1 | grep --line-buffered -v -i warn
.venv/bin/python -u code/make_judge_subset.py
.venv/bin/python -u code/judge.py mistral-7b results/gen/*.jsonl --subset results/labels/subset.json 2>&1 | grep --line-buffered -v -i warn
echo PIPELINE_DONE
