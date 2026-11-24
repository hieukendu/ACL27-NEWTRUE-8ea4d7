#!/bin/bash
# Round-1 fix: re-run stale retrieval with undated, neutral wording (rag_stale_u) for all 7 full-grid models (+ ancient control, id models).
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b qwen2.5-3b phi3.5-mini qwen2.5-7b mistral-7b; do
  .venv/bin/python -u code/run_generate.py $m --conds rag_stale_u 2>&1 | $F
done
for m in qwen2.5-3b qwen2.5-7b mistral-7b phi3.5-mini; do
  .venv/bin/python -u code/run_generate.py $m --items data/items_ancient.jsonl --conds rag_stale_u,cutoff_date,rag_mixed 2>&1 | $F
done
MAIN="results/gen/qwen2.5-0.5b.jsonl results/gen/qwen2.5-1.5b.jsonl results/gen/smollm2-1.7b.jsonl results/gen/qwen2.5-3b.jsonl results/gen/phi3.5-mini.jsonl results/gen/qwen2.5-7b.jsonl results/gen/mistral-7b.jsonl"
.venv/bin/python -u code/judge.py qwen2.5-7b $MAIN results/gen/*_anc.jsonl 2>&1 | $F
.venv/bin/python -u code/judge.py mistral-7b $MAIN results/gen/*_anc.jsonl 2>&1 | $F
echo PIPELINE7_DONE
