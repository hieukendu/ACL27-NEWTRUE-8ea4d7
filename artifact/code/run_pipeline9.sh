#!/bin/bash
# Round-2 revision (2026-11-18): T2-only controls (items_v3: true new / familiar false / unfamiliar false), corrected mixed
# retrieval, FreshQA's exact premise-check sentence, premise check + fresh evidence. All 7 full-grid models.
cd "$(dirname "$0")/.."
F="grep --line-buffered -v -i warn"
C3="plain,premise,premise_fq,premise_ragf,date,cutoff_date,rag_fresh,rag_mixed_u,rag_stale_u,policy,policy_nodate"
for m in qwen2.5-0.5b qwen2.5-1.5b smollm2-1.7b qwen2.5-3b phi3.5-mini qwen2.5-7b mistral-7b; do
  .venv/bin/python -u code/run_generate.py $m --items data/items_v3.jsonl --conds $C3 2>&1 | $F
  .venv/bin/python -u code/run_generate.py $m --conds premise_fq,premise_ragf,rag_mixed_u 2>&1 | $F
done
.venv/bin/python -u code/judge.py qwen2.5-7b results/gen/*_v3.jsonl results/gen/{qwen2.5-0.5b,qwen2.5-1.5b,smollm2-1.7b,qwen2.5-3b,phi3.5-mini,qwen2.5-7b,mistral-7b}.jsonl 2>&1 | $F
.venv/bin/python -u code/judge.py mistral-7b results/gen/*_v3.jsonl results/gen/{qwen2.5-0.5b,qwen2.5-1.5b,smollm2-1.7b,qwen2.5-3b,phi3.5-mini,qwen2.5-7b,mistral-7b}.jsonl 2>&1 | $F
echo PIPELINE9_DONE
