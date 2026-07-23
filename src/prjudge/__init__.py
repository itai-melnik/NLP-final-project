"""prjudge — judge-bias experimental pipeline.

All pipeline *logic* lives in this importable package. Scripts (scripts/) and
notebooks (notebooks/) are thin wrappers that configure and launch it.

Layout mirrors the spec stages:
  data.py     — Stage 0: selection filters over eval_100
  variants.py — Stage 1: the 9 perturbation constructors + invariance checks
  prompts.py  — frozen judge prompt/schema + verbosity-rewrite prompts (versioned)
  judge.py    — Stage 2: provider clients + resumable runner
  analysis.py — Stage 3: tidy DataFrame, aggregate score, flip rates, stats
  config.py   — shared config load + hashing + path resolution
"""

__version__ = "0.1.0"
