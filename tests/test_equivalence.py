"""Unit tests for the TOST equivalence / minimum-detectable-effect table.

The paper needs bounded-null claims ("effects larger than X are excluded"),
not bare non-significance. ``equivalence_by_axis`` must:
  * pass TOST (tost_p < .05) at a generous margin when the true effect is 0,
  * fail TOST at that margin when a real effect of that size exists,
  * report ``equiv_margin_min`` equal to the widest |bound| of the 90% CI
    (the smallest symmetric margin at which TOST would pass at alpha=.05),
  * report an 80%-power MDE that shrinks with n and grows with the SD.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge import analysis as A  # noqa: E402


def _tidy_df(deltas_by_pr: np.ndarray, variant: str = "placebo",
             axis: str = "placebo", judge: str = "claude") -> pd.DataFrame:
    """Minimal tidy results df: baseline + one variant, one trial per cell."""
    rows = []
    for i, d in enumerate(deltas_by_pr):
        tid = f"pr_{i:03d}"
        rows.append({"task_id": tid, "variant": "baseline", "axis": "baseline",
                     "judge": judge, "trial": 1, "aggregate": 5.0})
        rows.append({"task_id": tid, "variant": variant, "axis": axis,
                     "judge": judge, "trial": 1, "aggregate": 5.0 + d})
    return pd.DataFrame(rows)


def test_tost_passes_at_margin_when_no_true_effect():
    rng = np.random.default_rng(0)
    df = _tidy_df(rng.normal(0.0, 0.3, size=60))
    out = A.equivalence_by_axis(df, margin=0.5)
    row = out[(out["judge"] == "claude") & (out["axis"] == "placebo")].iloc[0]
    assert row["n"] == 60
    assert row["tost_p"] < 0.05  # equivalence established within ±0.5


def test_tost_fails_at_margin_when_effect_is_real():
    rng = np.random.default_rng(1)
    df = _tidy_df(rng.normal(0.6, 0.3, size=60))
    out = A.equivalence_by_axis(df, margin=0.5)
    row = out.iloc[0]
    assert row["tost_p"] > 0.05  # cannot claim |effect| < 0.5


def test_equiv_margin_min_is_widest_ci90_bound():
    rng = np.random.default_rng(2)
    df = _tidy_df(rng.normal(0.1, 0.4, size=40))
    row = A.equivalence_by_axis(df, margin=0.5).iloc[0]
    assert row["equiv_margin_min"] == max(abs(row["ci90_lo"]), abs(row["ci90_hi"]))
    assert row["ci90_lo"] < row["mean_delta"] < row["ci90_hi"]


def test_mde_shrinks_with_n_and_grows_with_sd():
    rng = np.random.default_rng(3)
    small = A.equivalence_by_axis(_tidy_df(rng.normal(0, 0.5, 20))).iloc[0]
    large = A.equivalence_by_axis(_tidy_df(rng.normal(0, 0.5, 90))).iloc[0]
    assert large["mde_80"] < small["mde_80"]
    # z-approx cross-check: MDE ≈ (z_.975 + z_.80) * sd / sqrt(n) = 2.80 sd/√n
    approx = 2.80 * large["sd_delta"] / np.sqrt(large["n"])
    assert abs(large["mde_80"] - approx) / approx < 0.05


def test_groups_by_judge_and_axis():
    rng = np.random.default_rng(4)
    df = pd.concat([
        _tidy_df(rng.normal(0, 0.3, 30), judge="claude"),
        _tidy_df(rng.normal(0, 0.3, 30), judge="gpt"),
    ])
    out = A.equivalence_by_axis(df)
    assert set(zip(out["judge"], out["axis"])) == {("claude", "placebo"), ("gpt", "placebo")}
