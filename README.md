# What Moves the Judge? — Judge-Bias Experimental Pipeline

Measures which **non-semantic** properties of a pull request move an LLM judge's
evaluation, holding the code change fixed and perturbing one surface property at
a time. Full design: [`docs/superpowers/specs/2026-07-23-judge-bias-pipeline-design.md`](docs/superpowers/specs/2026-07-23-judge-bias-pipeline-design.md).

## Structure

Hard separation of **preprocessing / experiment / analysis** (spec §7):

```
config/experiment.yaml   single source of truth (paths, seeds, filters, models, versions)
src/prjudge/             ALL logic (importable package)
scripts/                 thin CLI wrappers over the package
  00_build_selection.py  Stage 0 -> artifacts/selection_manifest_v1.json
  01_build_variants.py   Stage 1 -> artifacts/variants_v1/ + invariance_report_v1.json
  02_run_judges.py       Stage 2 -> artifacts/runs/{run_name}.jsonl
notebooks/
  10_experiment_runner.ipynb  thin: configure / dry-run / launch / monitor Stage 2
  20_analysis.ipynb           Stage 3: all stats, figures, tables (never calls an API)
artifacts/               frozen outputs, append-only, tracked in git
swe-prbench/             READ-ONLY dataset (gitignored, never modified)
```

**Convention:** notebooks for narrative, modules for logic. Stages 0–1 are
scripts only (freeze discipline); Stage 2 is a package + a thin launcher
notebook; Stage 3 is a pure notebook.

## Setup

Requires Python **3.12+** (developed on 3.13).

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # fill in API keys (only needed for real Stage-2 runs)
```

## Running the pipeline

```bash
# Stage 0 — frozen PR selection (n=41). Deterministic; re-run is byte-identical.
python scripts/00_build_selection.py

# Stage 1 — build the 9 variants per PR + invariance report. Fails loudly on
# any invariance violation. LLM verbosity rewrites are cached; --regenerate to redo.
python scripts/01_build_variants.py

# Stage 2 — judging. Resumable; keyed per cell; pilot runs never mix with final.
python scripts/02_run_judges.py --mock --run-name smoke        # no spend, tests keying/resume
python scripts/02_run_judges.py --dry-run                      # ~$0.10, real APIs, schema check
python scripts/02_run_judges.py --run-name results_v1          # full 3,321-call battery

# Stage 3 — analysis
jupyter notebook notebooks/20_analysis.ipynb
```

Run `python scripts/02_run_judges.py --help` for pilot / prompt-tuning options
(`--variants`, `--judges`, `--prs`, `--limit`, `--trials`, `--prompt-version`).

## Reproducibility

Every stage reads only the frozen artifact of the previous stage. Filters,
seeds, prompts, and model versions are pinned in `config/experiment.yaml`; each
artifact records the config hash it was built under. All raw judge responses are
retained in the JSONL. Any number in the paper is regenerable from artifacts.
