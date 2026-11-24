#!/bin/bash
# Round-2 scale-up on the GX10 server (NVIDIA GB10, CUDA): larger ungated models on the main grid and the entity triples.
# Run from ~/acl27/NEWTRUE after code/ and data/ are synced. Uses ~/acl27/venv. Results are copied back for judging.
cd "$(dirname "$0")/.."
PY=~/acl27/venv/bin/python
C="plain,premise,premise_fq,premise_ragf,date,cutoff_date,rag_fresh,rag_mixed_u,rag_stale_u,policy,policy_nodate"
for m in qwen2.5-14b phi4 qwen2.5-32b; do
  $PY -u code/run_generate.py $m --conds $C 2>&1 | grep --line-buffered -v -i warn
  $PY -u code/run_generate.py $m --items data/items_v3.jsonl --conds $C 2>&1 | grep --line-buffered -v -i warn
done
echo GX10_GEN_DONE
