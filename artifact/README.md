# Newly-True Presuppositions (ACL 2027 submission, ID ACL27-NEWTRUE-8ea4d7)

This project measures how often LLMs **wrongly rebut questions whose presupposition became true after their knowledge cutoff**, and how premise-checking interventions trade catching false premises against rebutting true ones.

## Environment
```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```
Hardware: Apple-silicon GPU (MPS), with one model process at a time. Models are loaded from the Hugging Face cache (see `code/lm.py`).

## Reproduction (in order)
```bash
# 1. data (network; cached in data/raw/)
python code/fetch_wikidata.py          # Wikidata SPARQL, 5 relations
python code/build_transitions.py       # transitions + long-standing holders
python code/build_items.py             # candidate items (5 conditions) + 439 date-probe transitions
python code/validate_items.py          # P39 office check + enwiki lead check -> data/items.jsonl (frozen 2026-11-10)
python code/make_data_appendix.py

# 2. GPU (sequential)
./code/run_all_probe.sh                # date probes -> results/probe/
./code/run_pipeline.sh                 # verifier, generation (7 conditions), sweeps, Qwen3.5 subset, judges

# 3. analysis, tables, figures, paper (final pipeline: see ../CHECKPOINT.md for the exact verified command)
python code/analyze_cutoff.py && python code/plot_cutoff.py
python code/analyze_main.py && python code/analyze_round1.py && python code/analyze_v2.py && python code/analyze_v3.py   # v3 runs analyze_v3_r3.py
python code/make_tables.py && python code/make_tables_v2.py && python code/make_tables_v3.py && python code/plot_figures_v2.py && python code/make_comic.py
python code/make_prompt_appendix.py && python code/make_examples.py && python code/plot_cutoff.py
python code/make_data_appendix.py
cd ../manuscript && latexmk -pdf main.tex
```

## Layout
- `data/items.jsonl`: the frozen benchmark (item IDs, Wikidata QIDs, condition, template, evidence snippets). `data/probe.jsonl`: the cutoff-probe set.
- `results/gen/`: raw generations. `results/labels/<judge>/`: judge labels. `results/verify/`: yes/no P(No). `results/probe/`: date-probe log-probabilities. `results/analysis/`: aggregated JSON.
- `PROVENANCE.md` maps every table, figure and in-text number to its script and result file. `STATUS.md` records what is real, what is pending, and the review scores.

## Licences
The data is derived from Wikidata (CC0) and English Wikipedia (CC BY-SA). The comic icons are from OpenMoji (CC BY-SA 4.0); see `figures/comic/ATTRIBUTION.md`.

## Environment variables
The code contains no machine-specific paths.
- `GPU_LOCK_DIR`: folder for the one-model-at-a-time GPU lock used by the run scripts (default `$TMPDIR/gpu_locks`).
- `ANTHROPIC_API_KEY` or `ANTHROPIC_KEY_FILE`: needed only to re-run the Claude judges.
- `OPENAI_API_KEY` or `OPENAI_KEY_FILE`: needed only to re-run the gpt-5.3-codex judge.

Machine paths in the logs are replaced by `<ACL_ROOT>`.
