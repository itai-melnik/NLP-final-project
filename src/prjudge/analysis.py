"""Stage 3 — analysis (pure pandas; never calls an API) (spec §6).

Loads a results JSONL into a tidy DataFrame, polarity-normalizes the checklist
to a 0–10 aggregate, and provides the analyses the paper reports: Δ vs same-PR
baseline, per-item flip rates, trial-to-trial noise floor, the placebo gate,
the verbosity trend, the self-preference 2×2, the item-9 / requested-changes
validity anchor, and hunk-based issue matching.

Every function takes/returns DataFrames so notebook 20 stays declarative.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import Config
from .data import load_annotation
from .prompts import CHECKLIST_ITEMS_V1
from .variants import VARIANT_AXIS

# Items where "yes" is unfavorable (spec §5.2) — flipped in polarity normalization.
UNFAVORABLE_ITEMS = {1, 5, 6, 9}
N_ITEMS = 10
ITEM_KEYS = [f"item_{i}" for i in range(1, N_ITEMS + 1)]


# ---------------------------------------------------------------------------
# Load → tidy DataFrame
# ---------------------------------------------------------------------------

def load_results(config: Config, run_name: str) -> pd.DataFrame:
    """Read a run's JSONL into a tidy per-call DataFrame with derived scores.

    One row per judge call. Adds per-item yes/no + polarity-normalized good_i
    (1 = favorable), the 0–10 aggregate, the axis label, and PR covariates from
    the selection manifest. Rows with unparseable output are dropped from the
    scored frame but counted in ``load_results.n_unparsed``.
    """
    path = config.artifacts_dir / "runs" / f"{run_name}.jsonl"
    rows: list[dict[str, Any]] = []
    n_unparsed = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            parsed = rec.get("parsed")
            if not parsed or "checklist" not in parsed:
                n_unparsed += 1
                continue
            row = {
                "task_id": rec["task_id"],
                "variant": rec["variant"],
                "judge": rec["judge"],
                "trial": rec["trial"],
                "axis": VARIANT_AXIS.get(rec["variant"], "unknown"),
                "issues": parsed.get("issues") or [],
                "justification": parsed.get("justification", ""),
            }
            ok = _expand_checklist(parsed["checklist"], row)
            if not ok:
                n_unparsed += 1
                continue
            rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = _attach_covariates(df, config)
    load_results.n_unparsed = n_unparsed  # type: ignore[attr-defined]
    return df


def _expand_checklist(checklist: dict, row: dict) -> bool:
    """Fill item_i (yes/no) and good_i (1=favorable) + aggregate. False if malformed."""
    good_total = 0
    for i, key in enumerate(ITEM_KEYS, start=1):
        item = checklist.get(key)
        if not isinstance(item, dict) or item.get("answer") not in ("yes", "no"):
            return False
        ans = item["answer"]
        row[f"item_{i}"] = ans
        favorable_yes = i not in UNFAVORABLE_ITEMS
        good = int((ans == "yes") == favorable_yes)
        row[f"good_{i}"] = good
        good_total += good
    row["aggregate"] = good_total
    return True


def _attach_covariates(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Merge per-PR covariates: manifest fields + requested_change_count from annotations.

    ``requested_change_count`` lives in the human annotations, not the PR record,
    so it is sourced here (the validity anchor, spec §6, correlates the aggregate
    against it).
    """
    manifest_path = config.artifacts_dir / f"selection_manifest_{config['versions']['selection']}.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        prs = json.load(f)["prs"]
    meta = pd.DataFrame(prs)[
        ["task_id", "difficulty", "language", "has_requested_changes", "short_desc"]
    ]
    # Pre-registered terse-infeasibility waivers (config: variants.terse_waivers,
    # spec §4.2/§8): their verb_terse cells are excluded from the terse arm.
    waivers = set(config["variants"].get("terse_waivers", []))
    meta["terse_waived"] = meta["task_id"].isin(waivers)
    # requested_change_count from annotations, per selected task.
    rcc = []
    for tid in meta["task_id"]:
        try:
            ann = load_annotation(config, tid)
            rcc.append({"task_id": tid, "requested_change_count": ann.get("requested_change_count")})
        except FileNotFoundError:
            rcc.append({"task_id": tid, "requested_change_count": None})
    meta = meta.merge(pd.DataFrame(rcc), on="task_id", how="left")
    return df.merge(meta, on="task_id", how="left")


# ---------------------------------------------------------------------------
# Per-cell aggregation helpers
# ---------------------------------------------------------------------------

def cell_means(df: pd.DataFrame) -> pd.DataFrame:
    """Mean aggregate per (task_id, variant, judge), averaged over trials."""
    return (df.groupby(["task_id", "variant", "judge", "axis"], as_index=False)["aggregate"]
              .mean().rename(columns={"aggregate": "mean_aggregate"}))


def deltas(df: pd.DataFrame) -> pd.DataFrame:
    """Δ(aggregate) = variant − same-PR baseline, per (task_id, judge, variant).

    Trial-averaged. The paired unit is (task_id, judge); baseline rows are dropped
    from the output (their Δ is 0 by construction).
    """
    cm = cell_means(df)
    base = (cm[cm["variant"] == "baseline"][["task_id", "judge", "mean_aggregate"]]
            .rename(columns={"mean_aggregate": "baseline_aggregate"}))
    merged = cm.merge(base, on=["task_id", "judge"], how="left")
    merged["delta"] = merged["mean_aggregate"] - merged["baseline_aggregate"]
    return merged[merged["variant"] != "baseline"].reset_index(drop=True)


def delta_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Median/mean |Δ| and signed Δ per (judge, axis) — the axis ranking table."""
    d = deltas(df)
    g = d.groupby(["judge", "axis"], as_index=False).agg(
        n=("delta", "size"),
        mean_delta=("delta", "mean"),
        median_delta=("delta", "median"),
        mean_abs_delta=("delta", lambda s: s.abs().mean()),
        median_abs_delta=("delta", lambda s: s.abs().median()),
    )
    return g.sort_values(["judge", "median_abs_delta"], ascending=[True, False]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Per-item flip rates + noise floor (spec §6)
# ---------------------------------------------------------------------------

def _modal_answers(df: pd.DataFrame) -> pd.DataFrame:
    """Modal (majority-over-trials) yes/no per (task_id, variant, judge, item)."""
    recs = []
    for (tid, variant, judge), grp in df.groupby(["task_id", "variant", "judge"]):
        rec = {"task_id": tid, "variant": variant, "judge": judge}
        for i in range(1, N_ITEMS + 1):
            vals = grp[f"item_{i}"]
            rec[f"item_{i}"] = vals.mode().iloc[0] if not vals.mode().empty else vals.iloc[0]
        recs.append(rec)
    return pd.DataFrame(recs)


def flip_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Per axis × item: rate the perturbation flips the modal answer vs baseline.

    Unit is (task_id, judge). This is the most interpretable output (spec §6):
    which judgments absorb each perturbation.
    """
    modal = _modal_answers(df)
    base = (modal[modal["variant"] == "baseline"]
            .drop(columns=["variant"])
            .set_index(["task_id", "judge"]))
    recs = []
    for variant in modal["variant"].unique():
        if variant == "baseline":
            continue
        sub = modal[modal["variant"] == variant].set_index(["task_id", "judge"])
        common = sub.index.intersection(base.index)
        for i in range(1, N_ITEMS + 1):
            col = f"item_{i}"
            flips = (sub.loc[common, col].values != base.loc[common, col].values)
            recs.append({
                "axis": VARIANT_AXIS.get(variant, "unknown"),
                "variant": variant,
                "item": i,
                "item_text": CHECKLIST_ITEMS_V1[i - 1],
                "n": len(common),
                "flip_rate": float(np.mean(flips)) if len(common) else float("nan"),
            })
    return pd.DataFrame(recs)


def modal_noise_floor(df: pd.DataFrame) -> pd.DataFrame:
    """Per-item rate the *modal* (majority-of-3) answer differs across two independent
    3-trial draws of the same cell — the correct noise reference for ``flip_rates()``
    (spec §6), since majority voting suppresses raw trial noise.

    Computed analytically per cell rather than via literal random resampling: for a
    cell with ``k`` "yes" out of ``m`` trials, resampling ``m`` trials with
    replacement from that cell is exactly ``Binomial(m, q=k/m)``, so the probability
    the modal answer of one such resample is "yes" is ``P(s > m/2)`` under that
    binomial (ties, only possible for even ``m``, resolve to "no" — matching
    ``pd.Series.mode().iloc[0]``'s alphabetical tie-break used in ``_modal_answers``).
    The probability two independent resamples disagree is then
    ``2 * p_yes * (1 - p_yes)``. This is algebraically identical to bootstrapping
    the two draws and comparing modes, just exact and RNG-free. Averaged over all
    (task_id, variant, judge) cells with >1 trial, matching ``noise_floor()``'s
    cell population.
    """
    from scipy.stats import binom  # noqa: PLC0415
    recs = []
    for i in range(1, N_ITEMS + 1):
        col = f"item_{i}"
        p_differ = []
        for _, grp in df.groupby(["task_id", "variant", "judge"]):
            m = len(grp)
            if m <= 1:
                continue
            k = int((grp[col] == "yes").sum())
            q = k / m
            p_yes = float(binom.sf(m / 2, m, q)) if q not in (0.0, 1.0) else float(q)
            p_differ.append(2 * p_yes * (1 - p_yes))
        recs.append({
            "item": i,
            "item_text": CHECKLIST_ITEMS_V1[i - 1],
            "n_cells": len(p_differ),
            "modal_noise_floor": float(np.mean(p_differ)) if p_differ else float("nan"),
        })
    return pd.DataFrame(recs)


def flip_rates_with_noise_floor(df: pd.DataFrame) -> pd.DataFrame:
    """``flip_rates()`` augmented with the modal noise floor and excess flip rate.

    Adds ``modal_noise_floor`` (see ``modal_noise_floor()``) and
    ``excess_flip_rate = flip_rate - modal_noise_floor`` per item. The placebo
    axis's own per-item flip rate is already present as a row (axis="placebo")
    and serves as an active-control reference alongside the noise floor — pivot
    on ``axis`` to compare both side by side (spec §6).
    """
    fr = flip_rates(df)
    mnf = modal_noise_floor(df)[["item", "modal_noise_floor"]]
    out = fr.merge(mnf, on="item", how="left")
    out["excess_flip_rate"] = out["flip_rate"] - out["modal_noise_floor"]
    return out


def noise_floor(df: pd.DataFrame) -> pd.DataFrame:
    """Trial-to-trial disagreement rate per item on identical input (spec §6).

    For each (task_id, variant, judge, item) with >1 trial, the item is "noisy"
    if the trials disagree. The per-item mean over all cells is the floor every
    flip rate is compared against.
    """
    recs = []
    for i in range(1, N_ITEMS + 1):
        col = f"item_{i}"
        disagreements = []
        for _, grp in df.groupby(["task_id", "variant", "judge"]):
            if len(grp) > 1:
                disagreements.append(grp[col].nunique() > 1)
        recs.append({
            "item": i,
            "item_text": CHECKLIST_ITEMS_V1[i - 1],
            "n_cells": len(disagreements),
            "noise_flip_rate": float(np.mean(disagreements)) if disagreements else float("nan"),
        })
    return pd.DataFrame(recs)


def _cell_trial_aggregates(df: pd.DataFrame, variant: str) -> dict[tuple[str, str], np.ndarray]:
    """Per (task_id, judge) array of trial-level ``aggregate`` values for one variant."""
    sub = df[df["variant"] == variant]
    out: dict[tuple[str, str], np.ndarray] = {}
    for (tid, judge), grp in sub.groupby(["task_id", "judge"]):
        out[(tid, judge)] = grp["aggregate"].to_numpy(dtype=float)
    return out


def _small_sample_scale(m: int) -> float:
    """Deviation-rescaling factor so resampling ``m`` points reproduces an unbiased
    sampling distribution for the mean, not just an unbiased *variance*.

    Two stacked small-sample corrections, both standard: (1) Bessel's correction
    (``sqrt(m/(m-1))``) makes the *variance* of the resampled mean unbiased for
    the population variance in expectation; but since the target statistic here
    is |Δ|, not Δ², a second, smaller correction is needed — with only ``m``
    (e.g. 3) points, the *realized* sample SD is itself a noisy, downward-biased
    estimator of the population SD (E[S] = c4(df)·σ, the classic control-chart
    "c4" factor, df = m−1), so |Δ_null| is systematically too small even after
    Bessel correction alone. Dividing by ``c4`` corrects for that. Verified
    empirically in ``tests/test_placebo_gate.py``: without this, the gate's
    Type-I rate is wildly off (~2–3% pass rate instead of ~95% under a true
    null); with it, pass rate is ~90–95%.
    """
    if m <= 1:
        return 1.0
    from scipy.special import gamma  # noqa: PLC0415
    dof = m - 1
    c4 = np.sqrt(2 / dof) * gamma((dof + 1) / 2) / gamma(dof / 2)
    return float(np.sqrt(m / (m - 1)) / c4)


def _bootstrap_delta_null(
    trial_map: dict[tuple[str, str], np.ndarray],
    keys: list[tuple[str, str]],
    *,
    n_boot: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Null distribution of mean|Δ_agg| from within-cell trial resampling.

    For each (task_id, judge) key, draws two independent pseudo-cells (same size
    as the cell's own trial count, with replacement) from that cell's observed
    trials (rescaled per ``_small_sample_scale`` to correct small-``m`` bias) and
    differences their means. One replicate = the mean over ``keys`` of |Δ_null|;
    returns the array of ``n_boot`` such replicate statistics.
    """
    per_key_abs_delta = np.empty((n_boot, len(keys)), dtype=float)
    for j, key in enumerate(keys):
        trials = trial_map[key]
        m = len(trials)
        mean = trials.mean()
        scale = _small_sample_scale(m)
        adjusted = mean + scale * (trials - mean)
        idx_a = rng.integers(0, m, size=(n_boot, m))
        idx_b = rng.integers(0, m, size=(n_boot, m))
        mean_a = adjusted[idx_a].mean(axis=1)
        mean_b = adjusted[idx_b].mean(axis=1)
        per_key_abs_delta[:, j] = np.abs(mean_a - mean_b)
    return per_key_abs_delta.mean(axis=1)


def placebo_gate(
    df: pd.DataFrame, *, n_boot: int = 10_000, seed: int = 0, pool_baseline_placebo: bool = False
) -> dict[str, Any]:
    """The placebo axis must show ≈0 effect; test |Δ| against an empirical noise null.

    The old gate compared placebo mean |Δ_agg| (a difference of two 3-trial means
    of a 10-item aggregate) to ``1.5 * noise_flip_rate`` (a single-item single-trial
    disagreement rate) — incompatible units, so it spuriously failed. This version
    builds the null for mean|Δ_agg| directly from the observed trial-to-trial
    variation: for each (task_id, judge) *baseline* cell (its 3 observed trials),
    draw two independent pseudo-cells by resampling trials with replacement and
    difference their means. Under H0 the placebo cells are exchangeable with
    baseline, so baseline-only resampling is valid; this implementation uses
    baseline trials only (not pooled with placebo) to keep the null uncontaminated
    by any possible placebo signal — pass ``pool_baseline_placebo=True`` to pool
    both into a larger resampling pool per cell instead.

    One bootstrap replicate draws one Δ_null per (task_id, judge) pair matching
    the placebo's own pairing structure (n≈80: PRs × judges) and takes the mean of
    |Δ_null| across pairs; the null distribution is built from ``n_boot`` such
    replicates. The gate passes iff the observed placebo mean|Δ| is at or below
    the null's 95th percentile (spec §6).

    With only 3 trials per cell, naive resampling-with-replacement is measurably
    biased low for |Δ| (verified in ``tests/test_placebo_gate.py``: an
    uncorrected version passes a true null only ~2–3% of the time, i.e. it
    reproduces the *original* bug's symptom of an almost-always-failing gate).
    ``_bootstrap_delta_null`` applies a standard small-sample correction
    (``_small_sample_scale``) so the null is calibrated to ~90–95% under a true
    null in the synthetic test.
    """
    d = deltas(df)
    placebo = d[d["variant"] == "placebo"]
    placebo_delta = placebo["delta"]
    observed_mean_abs = float(placebo_delta.abs().mean()) if len(placebo_delta) else float("nan")
    observed_median_abs = float(placebo_delta.abs().median()) if len(placebo_delta) else float("nan")

    baseline_map = _cell_trial_aggregates(df, "baseline")
    if pool_baseline_placebo:
        placebo_map = _cell_trial_aggregates(df, "placebo")
        pooled_map = {
            key: np.concatenate([baseline_map[key], placebo_map[key]]) if key in placebo_map else trials
            for key, trials in baseline_map.items()
        }
        trial_map = pooled_map
    else:
        trial_map = baseline_map

    keys = [(row.task_id, row.judge) for row in placebo.itertuples() if (row.task_id, row.judge) in trial_map]
    rng = np.random.default_rng(seed)
    null_stats = (
        _bootstrap_delta_null(trial_map, keys, n_boot=n_boot, rng=rng)
        if keys else np.array([np.nan])
    )
    null_mean = float(np.mean(null_stats))
    null_p95 = float(np.percentile(null_stats, 95))
    p_value = float(np.mean(null_stats >= observed_mean_abs)) if not np.isnan(observed_mean_abs) else float("nan")
    passes = bool(observed_mean_abs <= null_p95) if not np.isnan(observed_mean_abs + null_p95) else False

    nf = noise_floor(df)["noise_flip_rate"].mean()

    from scipy.stats import wilcoxon  # noqa: PLC0415
    signed_effect_by_judge: dict[str, dict[str, Any]] = {}
    for judge, grp in placebo.groupby("judge"):
        vals = grp["delta"].dropna().values
        if len(vals) >= 5 and np.any(vals != 0):
            try:
                _, wp = wilcoxon(vals)
            except ValueError:
                wp = float("nan")
        else:
            wp = float("nan")
        signed_effect_by_judge[judge] = {
            "mean_delta": float(np.mean(vals)) if len(vals) else float("nan"),
            "wilcoxon_p": float(wp),
            "n": int(len(vals)),
        }

    return {
        "observed_mean_abs_delta": observed_mean_abs,
        "observed_median_abs_delta": observed_median_abs,
        "null_mean_abs_delta": null_mean,
        "null_p95_abs_delta": null_p95,
        "p_value": p_value,
        "passes": passes,
        "n": int(len(keys)),
        "n_boot": int(n_boot),
        "noise_floor_mean_item_rate": float(nf),
        "signed_effect_by_judge": signed_effect_by_judge,
    }


# ---------------------------------------------------------------------------
# Verbosity trend (spec §6)
# ---------------------------------------------------------------------------

VERBOSITY_ORDER = ["verb_terse", "baseline", "verb_pad2x", "verb_pad4x"]


def verbosity_trend(
    df: pd.DataFrame, *, exclude_short_desc: bool = False, exclude_terse_waived: bool = True
) -> pd.DataFrame:
    """Mean aggregate across terse < baseline < 2× < 4×, per judge, + Spearman trend.

    A monotonic score-vs-length trend is the target evidence (spec §4.1). Set
    ``exclude_short_desc`` for the sensitivity check that drops the 4 short-desc PRs.
    ``exclude_terse_waived`` (default, pre-registered §4.2/§8) drops only the
    verb_terse cells of terse-waived PRs — their rewrites could not reach the
    0.5x band, so those cells carry no terse dose; baseline/pad cells stay in.
    """
    from scipy.stats import spearmanr  # noqa: PLC0415
    sub = df[df["variant"].isin(VERBOSITY_ORDER)].copy()
    if exclude_short_desc:
        sub = sub[~sub["short_desc"].fillna(False)]
    if exclude_terse_waived and "terse_waived" in sub.columns:
        sub = sub[~((sub["variant"] == "verb_terse") & sub["terse_waived"].fillna(False))]
    sub["dose"] = sub["variant"].map({v: i for i, v in enumerate(VERBOSITY_ORDER)})
    recs = []
    for judge, grp in sub.groupby("judge"):
        means = grp.groupby("variant")["aggregate"].mean().reindex(VERBOSITY_ORDER)
        rho, p = spearmanr(grp["dose"], grp["aggregate"])
        rec = {"judge": judge, "spearman_rho": float(rho), "spearman_p": float(p)}
        for v in VERBOSITY_ORDER:
            rec[f"mean_{v}"] = float(means.get(v, float("nan")))
        recs.append(rec)
    return pd.DataFrame(recs)


# ---------------------------------------------------------------------------
# Self-preference 2×2 (spec §6)
# ---------------------------------------------------------------------------

def self_preference(df: pd.DataFrame) -> pd.DataFrame:
    """Claimed-family × judge-family Δ table; interaction = self-preference estimate.

    For each judge, Δ for origin_claude and origin_gpt vs baseline. A judge that
    favors its own family shows a positive Δ when the claimed family matches it.
    """
    d = deltas(df)
    sub = d[d["variant"].isin(["origin_claude", "origin_gpt"])]
    tab = sub.groupby(["judge", "variant"], as_index=False)["delta"].mean()
    pivot = tab.pivot(index="judge", columns="variant", values="delta").reset_index()
    if "origin_claude" in pivot and "origin_gpt" in pivot:
        # Own-minus-other contrast per judge family (interpretation is per-judge).
        pivot["claude_minus_gpt"] = pivot["origin_claude"] - pivot["origin_gpt"]
    return pivot


# ---------------------------------------------------------------------------
# Placebo-as-active-control view (secondary; spec §6)
# ---------------------------------------------------------------------------

def placebo_active_control(df: pd.DataFrame) -> pd.DataFrame:
    """Per (judge, axis): Δ_axis vs the same judge's Δ_placebo, paired per-PR.

    SECONDARY VIEW — does not replace the primary Δ-vs-baseline analysis
    (``delta_summary`` / ``wilcoxon_by_axis`` / ``mixedlm_by_axis``). Since the
    placebo gate (``placebo_gate()``) shows the placebo axis itself sits near the
    noise floor rather than at a true zero, this reframes each axis's effect
    against that active (non-zero-null) control instead of against zero: for each
    (task_id, judge, axis-variant) row, differences against that task_id's own
    Δ_placebo, then a paired Wilcoxon on those per-PR differences (spec §6).
    """
    from scipy.stats import wilcoxon  # noqa: PLC0415
    d = deltas(df)
    placebo = (d[d["variant"] == "placebo"][["task_id", "judge", "delta"]]
               .rename(columns={"delta": "delta_placebo"}))
    axes = d[d["axis"] != "placebo"]
    recs = []
    for (judge, axis), grp in axes.groupby(["judge", "axis"]):
        merged = grp.merge(placebo[placebo["judge"] == judge][["task_id", "delta_placebo"]],
                            on="task_id", how="inner")
        if merged.empty:
            continue
        diff = (merged["delta"] - merged["delta_placebo"]).dropna().values
        if len(diff) >= 5 and np.any(diff != 0):
            try:
                stat, p = wilcoxon(diff)
            except ValueError:
                stat, p = float("nan"), float("nan")
        else:
            stat, p = float("nan"), float("nan")
        recs.append({
            "judge": judge, "axis": axis, "n": len(diff),
            "mean_delta_axis": float(merged["delta"].mean()),
            "mean_delta_placebo": float(merged["delta_placebo"].mean()),
            "mean_diff_vs_placebo": float(np.mean(diff)) if len(diff) else float("nan"),
            "median_diff_vs_placebo": float(np.median(diff)) if len(diff) else float("nan"),
            "wilcoxon_stat": float(stat), "wilcoxon_p": float(p),
        })
    return pd.DataFrame(recs)


# ---------------------------------------------------------------------------
# Validity anchor: item 9 vs has_requested_changes (spec §6)
# ---------------------------------------------------------------------------

def cohen_kappa(a: pd.Series, b: pd.Series) -> float:
    """Cohen's κ for two binary label series (chance-corrected agreement).

    κ = (p_o − p_e) / (1 − p_e), with p_o the observed agreement rate and p_e the
    agreement expected from the two marginals alone. Implemented directly (no
    sklearn dependency — not in requirements.txt) since inputs are binary.
    Raw agreement can look reasonable while κ is negative when the marginals are
    lopsided in opposite directions (spec §6).
    """
    a = pd.Series(a).astype(bool).reset_index(drop=True)
    b = pd.Series(b).astype(bool).reset_index(drop=True)
    n = len(a)
    if n == 0:
        return float("nan")
    p_o = float((a == b).mean())
    p_a1 = float(a.mean())
    p_b1 = float(b.mean())
    p_e = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
    if p_e >= 1.0:
        return float("nan")
    return (p_o - p_e) / (1 - p_e)


def item9_validity(df: pd.DataFrame) -> pd.DataFrame:
    """Baseline item-9 ("would request changes") vs human has_requested_changes.

    Direct binary agreement per judge, plus Spearman of the baseline aggregate
    with requested_change_count.
    """
    from scipy.stats import spearmanr  # noqa: PLC0415
    base = df[df["variant"] == "baseline"].copy()
    # Modal item-9 per (task_id, judge).
    recs = []
    for judge, grp in base.groupby("judge"):
        modal = (grp.groupby("task_id")
                    .agg(item9=("item_9", lambda s: s.mode().iloc[0]),
                         agg=("aggregate", "mean"),
                         hrc=("has_requested_changes", "first"),
                         rcc=("requested_change_count", "first"))
                    .reset_index())
        modal["judge_flag"] = modal["item9"] == "yes"
        modal["human_flag"] = modal["hrc"].astype("boolean").fillna(False)
        agreement = float((modal["judge_flag"] == modal["human_flag"]).mean())
        kappa = cohen_kappa(modal["judge_flag"], modal["human_flag"])
        rcc = pd.to_numeric(modal["rcc"], errors="coerce")
        valid = rcc.notna()
        rho, p = (spearmanr(modal["agg"][valid], rcc[valid]) if valid.sum() > 2 else (float("nan"),) * 2)
        recs.append({
            "judge": judge,
            "n": len(modal),
            "item9_vs_human_agreement": agreement,
            "item9_vs_human_kappa": kappa,
            "judge_request_rate": float(modal["judge_flag"].mean()),
            "human_request_rate": float(modal["human_flag"].mean()),
            "spearman_agg_vs_reqcount": float(rho),
            "spearman_p": float(p),
        })
    return pd.DataFrame(recs)


# ---------------------------------------------------------------------------
# Issue matching (secondary; spec §6)
# ---------------------------------------------------------------------------

_HUNK_RE = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _hunk_range(diff_hunk: str) -> tuple[int, int] | None:
    """Post-image line range (start, end) from a diff_hunk header, or None."""
    m = _HUNK_RE.search(diff_hunk or "")
    if not m:
        return None
    start = int(m.group(1))
    length = int(m.group(2)) if m.group(2) else 1
    return start, start + max(0, length - 1)


def human_issue_locations(config: Config, task_id: str) -> list[dict[str, Any]]:
    """Human-flagged (file, line-range) locations from the annotation's requires_change comments."""
    ann = load_annotation(config, task_id)
    out = []
    for c in ann.get("comments", []):
        if not c.get("file"):
            continue
        rng = _hunk_range(c.get("diff_hunk", ""))
        out.append({
            "file": c["file"],
            "line": c.get("line"),
            "range": rng,
            "requires_change": bool(c.get("requires_change")),
        })
    return out


def _issue_matches(issue: dict, human_locs: list[dict]) -> bool:
    """A judge issue matches a human location if same file and line in the hunk range."""
    ifile = (issue.get("file") or "").strip()
    iline = issue.get("approx_line")
    for h in human_locs:
        if not ifile or not h["file"]:
            continue
        if ifile != h["file"] and not (ifile.endswith(h["file"]) or h["file"].endswith(ifile)):
            continue
        rng = h["range"]
        if rng is None or not isinstance(iline, (int, float)):
            return True  # file match with no usable line range → count as a hit
        if rng[0] <= int(iline) <= rng[1]:
            return True
    return False


def issue_matching(config: Config, df: pd.DataFrame) -> pd.DataFrame:
    """Detection overlap with human reviewers, per (judge, variant).

    At baseline this is validity evidence; under perturbation the shift shows
    whether the judge stops seeing human-flagged issues (spec §6). Detection is
    scored per (task_id, judge, variant): did any reported issue match any human
    location, averaged over trials then over PRs.
    """
    human_cache: dict[str, list[dict]] = {}
    recs = []
    for (tid, variant, judge), grp in df.groupby(["task_id", "variant", "judge"]):
        if tid not in human_cache:
            try:
                human_cache[tid] = human_issue_locations(config, tid)
            except FileNotFoundError:
                human_cache[tid] = []
        locs = human_cache[tid]
        # Per-trial detection, then average → detection propensity for this cell.
        trial_hits = []
        for _, r in grp.iterrows():
            issues = r["issues"] or []
            trial_hits.append(any(_issue_matches(iss, locs) for iss in issues))
        recs.append({
            "task_id": tid, "variant": variant, "judge": judge,
            "axis": VARIANT_AXIS.get(variant, "unknown"),
            "detection": float(np.mean(trial_hits)) if trial_hits else 0.0,
            "n_human_locs": len(locs),
        })
    cell = pd.DataFrame(recs)
    return (cell.groupby(["judge", "variant", "axis"], as_index=False)["detection"]
                .mean().sort_values(["judge", "variant"]).reset_index(drop=True))


# ---------------------------------------------------------------------------
# Inferential stats (spec §6)
# ---------------------------------------------------------------------------

def bh_adjust(pvalues: pd.Series | np.ndarray) -> np.ndarray:
    """Benjamini–Hochberg adjusted p-values (FDR control) for an array of raw p's.

    NaNs pass through as NaN and are excluded from the correction (they aren't a
    tested hypothesis). Standard step-up procedure: sort ascending, adjust by
    ``m/rank``, then enforce monotonicity by a running minimum from the largest
    p-value down, and clip to 1 (spec §6 multiplicity correction).
    """
    p = np.asarray(pvalues, dtype=float)
    out = np.full(p.shape, np.nan)
    mask = ~np.isnan(p)
    valid = p[mask]
    m = len(valid)
    if m == 0:
        return out
    order = np.argsort(valid)
    ranked = valid[order]
    adj = ranked * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    out_valid = np.empty(m)
    out_valid[order] = adj
    out[mask] = out_valid
    return out


def wilcoxon_by_axis(df: pd.DataFrame) -> pd.DataFrame:
    """Wilcoxon signed-rank on Δ per (judge, axis) — robustness check for the mixed model.

    ``p_adj_bh`` is the Benjamini–Hochberg adjusted p-value within each judge
    (correcting across that judge's axes); ``p_value`` is kept unadjusted.
    """
    from scipy.stats import wilcoxon  # noqa: PLC0415
    d = deltas(df)
    recs = []
    for (judge, axis), grp in d.groupby(["judge", "axis"]):
        vals = grp["delta"].dropna().values
        if len(vals) >= 5 and np.any(vals != 0):
            try:
                stat, p = wilcoxon(vals)
            except ValueError:
                stat, p = float("nan"), float("nan")
        else:
            stat, p = float("nan"), float("nan")
        recs.append({"judge": judge, "axis": axis, "n": len(vals),
                     "median_delta": float(np.median(vals)) if len(vals) else float("nan"),
                     "wilcoxon_stat": float(stat), "p_value": float(p)})
    out = pd.DataFrame(recs)
    if not out.empty:
        out["p_adj_bh"] = out.groupby("judge")["p_value"].transform(lambda s: bh_adjust(s))
    return out


def mixedlm_by_axis(df: pd.DataFrame) -> pd.DataFrame:
    """Mixed-effects estimate of the axis effect with PR as random intercept (spec §6).

    Fits ``aggregate ~ C(variant)`` with a per-PR random intercept, per judge over
    baseline + that axis's variants. Returns each variant's fixed-effect estimate
    (Δ vs baseline) with p-value. Falls back to NaN rows if statsmodels is absent.
    """
    try:
        import statsmodels.formula.api as smf  # noqa: PLC0415
    except ImportError:
        return pd.DataFrame()
    recs = []
    for judge in sorted(df["judge"].unique()):
        jd = df[df["judge"] == judge]
        for axis in sorted(a for a in jd["axis"].unique() if a not in ("baseline",)):
            variants = [v for v, a in VARIANT_AXIS.items() if a == axis]
            sub = jd[jd["variant"].isin(["baseline"] + variants)].copy()
            if sub["variant"].nunique() < 2 or sub["task_id"].nunique() < 3:
                continue
            sub["variant"] = pd.Categorical(
                sub["variant"], categories=["baseline"] + variants, ordered=False)
            try:
                model = smf.mixedlm("aggregate ~ C(variant)", sub, groups=sub["task_id"])
                res = model.fit(reml=False, method="lbfgs", disp=False)
            except Exception as e:  # noqa: BLE001 — singular fits happen on thin cells
                recs.append({"judge": judge, "axis": axis, "term": "FIT_ERROR",
                             "estimate": float("nan"), "p_value": float("nan"),
                             "note": str(e)[:80]})
                continue
            for term in res.params.index:
                if term.startswith("C(variant)"):
                    recs.append({
                        "judge": judge, "axis": axis,
                        "term": term.replace("C(variant)[T.", "").rstrip("]"),
                        "estimate": float(res.params[term]),
                        "p_value": float(res.pvalues[term]),
                        "note": "",
                    })
    out = pd.DataFrame(recs)
    if not out.empty:
        # p_adj_bh: BH-adjusted within judge, across that judge's terms (excludes
        # FIT_ERROR rows, which carry no p-value to correct).
        out["p_adj_bh"] = out.groupby("judge")["p_value"].transform(lambda s: bh_adjust(s))
    return out


# ---------------------------------------------------------------------------
# Figures / output
# ---------------------------------------------------------------------------

def figures_dir(config: Config) -> Path:
    d = config.artifacts_dir / "figures"
    d.mkdir(parents=True, exist_ok=True)
    return d
