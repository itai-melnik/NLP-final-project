"""Unit tests for Tier-A issue-level validity: comment-level recall + issue-level precision.

Unit of analysis is the individual human comment (recall) / judge issue
(precision), not the PR-cell binary of ``issue_matching``. Matching rule is the
existing location rule (same file, line within the comment's hunk range).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge import analysis as A  # noqa: E402


def _row(task, judge, variant, trial, issues):
    return {"task_id": task, "judge": judge, "variant": variant, "trial": trial,
            "issues": issues}


UNITS = {
    "pr_a": [
        {"file": "src/x.py", "line": 12, "range": (10, 20), "requires_change": True},
        {"file": "src/y.py", "line": 5, "range": (1, 8), "requires_change": False},
    ],
}
ISSUE_HIT_X = {"file": "src/x.py", "approx_line": 15, "description": "bug"}
ISSUE_MISS = {"file": "src/z.py", "approx_line": 3, "description": "unrelated"}


def test_perfect_recall_and_precision():
    df = pd.DataFrame([_row("pr_a", "claude", "baseline", 1, [
        {"file": "src/x.py", "approx_line": 12, "description": "a"},
        {"file": "src/y.py", "approx_line": 5, "description": "b"},
    ])])
    out = A.issue_recall_precision(df, UNITS)
    r = out.iloc[0]
    assert r["recall"] == 1.0 and r["precision"] == 1.0
    assert r["n_human_units"] == 2 and r["n_judge_issues"] == 2.0  # 2 issues in 1 trial


def test_partial_recall_counts_unmatched_units():
    df = pd.DataFrame([_row("pr_a", "claude", "baseline", 1, [ISSUE_HIT_X])])
    r = A.issue_recall_precision(df, UNITS).iloc[0]
    assert r["recall"] == 0.5      # y.py comment never matched
    assert r["precision"] == 1.0   # the one issue did land


def test_precision_counts_unmatched_issues():
    df = pd.DataFrame([_row("pr_a", "claude", "baseline", 1, [ISSUE_HIT_X, ISSUE_MISS])])
    r = A.issue_recall_precision(df, UNITS).iloc[0]
    assert r["precision"] == 0.5


def test_trial_averaging_gives_match_propensity():
    df = pd.DataFrame([
        _row("pr_a", "claude", "baseline", 1, [ISSUE_HIT_X]),
        _row("pr_a", "claude", "baseline", 2, []),
    ])
    r = A.issue_recall_precision(df, UNITS).iloc[0]
    assert r["recall"] == 0.25     # x.py matched in 1/2 trials, y.py in 0/2


def test_groups_by_judge_and_variant():
    df = pd.DataFrame([
        _row("pr_a", "claude", "baseline", 1, [ISSUE_HIT_X]),
        _row("pr_a", "gpt", "verb_pad2x", 1, [ISSUE_MISS]),
    ])
    out = A.issue_recall_precision(df, UNITS)
    assert set(zip(out["judge"], out["variant"])) == {("claude", "baseline"), ("gpt", "verb_pad2x")}
    gpt = out[out["judge"] == "gpt"].iloc[0]
    assert gpt["recall"] == 0.0 and gpt["precision"] == 0.0
