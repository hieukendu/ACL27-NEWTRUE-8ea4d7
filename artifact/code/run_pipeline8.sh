#!/bin/bash
# Round-1: extend the new baselines and the entity-matched ancient control to the 3 small models, so all claims use all 7 models.
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b; do
  .venv/bin/python -u code/run_generate.py $m --conds cutoff_date,rag_mixed 2>&1 | $F
  .venv/bin/python -u code/run_generate.py $m --items data/items_ancient.jsonl --conds plain,premise,date,rag_fresh,rag_stale,policy,policy_nodate,rag_stale_u,cutoff_date,rag_mixed 2>&1 | $F
done
MAIN="results/gen/qwen2.5-0.5b.jsonl results/gen/qwen2.5-1.5b.jsonl results/gen/smollm2-1.7b.jsonl"
.venv/bin/python -u code/judge.py qwen2.5-7b $MAIN results/gen/*_anc.jsonl 2>&1 | $F
.venv/bin/python -u code/judge.py mistral-7b $MAIN results/gen/*_anc.jsonl 2>&1 | $F
echo PIPELINE8_DONE
