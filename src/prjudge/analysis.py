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


def placebo_gate(df: pd.DataFrame) -> dict[str, Any]:
    """The placebo axis must show ≈0 effect; compare |Δ| to the aggregate noise floor.

    Returns the placebo mean |Δ|, a noise-floor reference, and a pass flag. A
    failing gate means the noise model is wrong and results should not be reported
    until resolved (spec §6).
    """
    d = deltas(df)
    placebo = d[d["variant"] == "placebo"]["delta"]
    nf = noise_floor(df)["noise_flip_rate"].mean()
    mean_abs = float(placebo.abs().mean()) if len(placebo) else float("nan")
    # Reference band: mean absolute Δ expected from pure trial noise is ~ nf (items
    # flip ~nf of the time, each worth 1 point). Gate: placebo |Δ| within ~1.5x.
    reference = 1.5 * nf if not np.isnan(nf) else float("nan")
    return {
        "placebo_mean_abs_delta": mean_abs,
        "placebo_median_abs_delta": float(placebo.abs().median()) if len(placebo) else float("nan"),
        "noise_floor_mean_item_rate": float(nf),
        "reference_band": float(reference),
        "passes": bool(mean_abs <= reference) if not np.isnan(mean_abs + reference) else False,
        "n": int(len(placebo)),
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
    The open judge is the neutral control.
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
# Validity anchor: item 9 vs has_requested_changes (spec §6)
# ---------------------------------------------------------------------------

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
        rcc = pd.to_numeric(modal["rcc"], errors="coerce")
        valid = rcc.notna()
        rho, p = (spearmanr(modal["agg"][valid], rcc[valid]) if valid.sum() > 2 else (float("nan"),) * 2)
        recs.append({
            "judge": judge,
            "n": len(modal),
            "item9_vs_human_agreement": agreement,
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

def wilcoxon_by_axis(df: pd.DataFrame) -> pd.DataFrame:
    """Wilcoxon signed-rank on Δ per (judge, axis) — robustness check for the mixed model."""
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
    return pd.DataFrame(recs)


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
    return pd.DataFrame(recs)


# ---------------------------------------------------------------------------
# Figures / output
# ---------------------------------------------------------------------------

def figures_dir(config: Config) -> Path:
    d = config.artifacts_dir / "figures"
    d.mkdir(parents=True, exist_ok=True)
    return d
