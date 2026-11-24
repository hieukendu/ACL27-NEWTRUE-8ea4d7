# ACL27-NEWTRUE-8ea4d7

Layout (restructured 2026-11-18):
- `artifact/`: code, data, results, Python environment(s), requirements, README (reproduction) and PROVENANCE.
  Run all code commands **from `artifact/`** (e.g. `cd artifact && source .venv/bin/activate && python code/...`).
  `artifact/figures`, `artifact/tables`, `artifact/sections` and the macro files are links into `manuscript/`, so the
  scripts write generated figures, tables and macros directly into the paper.
- `manuscript/`: LaTeX sources (`main.tex`, `sections/`, `figures/`, `tables/`, `refs.bib`, ACL style files) and `main.pdf`.
  Build with `cd manuscript && latexmk -pdf main.tex`.
- `reviews/`, `STATUS.md`, `CHECKPOINT.md`: review rounds and project status.

Paths in older notes (CHECKPOINT/STATUS/PROVENANCE) that say "from the paper folder" now mean `artifact/` for code and `manuscript/` for LaTeX.
