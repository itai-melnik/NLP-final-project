"""Stage 0 — data loading + PR selection (spec §3).

Loads the eval_100 pool, applies the four frozen selection filters, and produces
the selection manifest. Also hosts the diff-parsing helpers shared with
``variants.py`` (file listing, test/non-test classification, per-file section
splitting for the file-order axis).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

from .config import Config

# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_eval_pool(config: Config) -> list[dict[str, Any]]:
    """The 100 curated ids in evals/eval_100.json — full PR records (incl. diff)."""
    with open(config.path("eval_100"), "r", encoding="utf-8") as f:
        return json.load(f)


def load_prs(config: Config) -> dict[str, dict[str, Any]]:
    """All 350 PR records from prs.jsonl, keyed by task_id."""
    out: dict[str, dict[str, Any]] = {}
    with open(config.path("prs_jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out[rec["task_id"]] = rec
    return out


def load_annotation(config: Config, task_id: str) -> dict[str, Any]:
    """Human-annotation record for one task (issue locations, requested changes)."""
    p = config.path("annotations_dir") / f"{task_id}_human.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Diff parsing (shared with variants.py)
# ---------------------------------------------------------------------------

_DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)


def diff_files(diff: str) -> list[str]:
    """Post-image file paths (the ``b/`` side) of every ``diff --git`` header."""
    return [m.group(2) for m in _DIFF_GIT_RE.finditer(diff)]


# Path is a test file if any of these hold (matches the design's test/non-test mix).
_TEST_DIR_RE = re.compile(r"(^|/)(tests?|__tests__|testing|spec|specs)(/|$)")
_TEST_BASENAME_RE = re.compile(
    r"(^test[_.].*|.*[_.]test\.[^/]+$|.*[_.]spec\.[^/]+$|.*\.test\.[^/]+$|.*\.spec\.[^/]+$|test_.*\.py$|.*_test\.(py|go)$)"
)


def is_test_file(path: str) -> bool:
    """Classify a file path as a test file (dir- or basename-based heuristic)."""
    p = path.lower()
    base = p.rsplit("/", 1)[-1]
    if _TEST_DIR_RE.search(p):
        return True
    if "test" in base or "spec" in base:
        # tighten: 'test'/'spec' as a token, not e.g. 'latest.py' / 'respect.js'
        if _TEST_BASENAME_RE.search(base) or base.startswith("test"):
            return True
    return False


@dataclass(frozen=True)
class DiffSection:
    """One per-file section of a unified diff, from its ``diff --git`` line to the next."""
    path: str          # post-image path (b/ side)
    text: str          # full section text, including trailing newline handling


def split_diff_sections(diff: str) -> list[DiffSection]:
    """Split a unified diff into per-file sections in file order.

    A section runs from one ``diff --git`` header line up to (but not including)
    the next. Reassembling ``"".join(s.text for s in sections)`` reproduces the
    original diff exactly. (Was the basis of the order_rev axis, dropped in
    variants v2; kept as a general diff utility.)
    """
    lines = diff.splitlines(keepends=True)
    sections: list[DiffSection] = []
    cur_start: int | None = None
    cur_path: str | None = None
    for i, line in enumerate(lines):
        m = re.match(r"^diff --git a/(.+?) b/(.+?)\r?\n?$", line)
        if m:
            if cur_start is not None:
                sections.append(DiffSection(cur_path, "".join(lines[cur_start:i])))
            cur_start = i
            cur_path = m.group(2)
    if cur_start is not None:
        sections.append(DiffSection(cur_path, "".join(lines[cur_start:])))
    return sections


# ---------------------------------------------------------------------------
# Selection filters (spec §3)
# ---------------------------------------------------------------------------

@dataclass
class FilterResult:
    passed: bool
    reasons: list[str]      # which filters the PR failed (empty if passed)


def evaluate_filters(rec: dict[str, Any], config: Config) -> FilterResult:
    """Apply the frozen selection filters to one PR record."""
    s = config["selection"]
    reasons: list[str] = []

    # v2: judge-visibility filter — only PRs whose human-flagged issues are
    # directly visible in the diff (the judge's whole input). See spec §8.
    want_difficulty = s.get("require_difficulty")
    if want_difficulty and rec.get("difficulty") != want_difficulty:
        reasons.append("difficulty_not_" + want_difficulty.lower())

    desc = (rec.get("description") or "").strip()
    if len(desc) < s["min_description_chars"]:
        reasons.append("description_too_short")

    diff = rec.get("diff_patch") or ""
    if len(diff) > s["max_diff_chars"]:
        reasons.append("diff_too_large")

    files = diff_files(diff)
    if len(files) < s["min_file_sections"]:
        reasons.append("too_few_files")
    elif s.get("require_test_nontest_mix", True):
        tests = [f for f in files if is_test_file(f)]
        nontests = [f for f in files if not is_test_file(f)]
        if not (tests and nontests):
            reasons.append("no_test_nontest_mix")

    if rec["task_id"] in set(s.get("drop_list", [])):
        reasons.append("ai_authorship_droplist")

    return FilterResult(passed=not reasons, reasons=reasons)


def pr_metadata_snapshot(rec: dict[str, Any], config: Config) -> dict[str, Any]:
    """Per-PR metadata frozen into the manifest (spec §3 frozen artifact)."""
    desc = (rec.get("description") or "").strip()
    files = diff_files(rec.get("diff_patch") or "")
    return {
        "task_id": rec["task_id"],
        "repo": rec["repo"],
        "pr_number": rec["pr_number"],
        "language": rec.get("language"),
        "difficulty": rec.get("difficulty"),
        "has_requested_changes": rec.get("has_requested_changes"),
        "description_chars": len(desc),
        "diff_chars": len(rec.get("diff_patch") or ""),
        "n_files": len(files),
        "n_test_files": sum(1 for f in files if is_test_file(f)),
        "short_desc": len(desc) < config["selection"]["short_description_chars"],
    }


def select_prs(config: Config) -> dict[str, Any]:
    """Run selection over the eval_100 pool and return the manifest payload.

    Returns a dict ready to serialize as ``selection_manifest_v1.json``:
    task_ids (sorted), per-PR metadata snapshots, filter params, config hash,
    and composition counts for the audit check.
    """
    pool = load_eval_pool(config)
    selected: list[dict[str, Any]] = []
    for rec in pool:
        if evaluate_filters(rec, config).passed:
            selected.append(rec)

    selected.sort(key=lambda r: r["task_id"])
    metadata = [pr_metadata_snapshot(r, config) for r in selected]

    return {
        "version": config["versions"]["selection"],
        "config_hash": config.hash(),
        "seed": config["seed"],
        "pool_size": len(pool),
        "n_selected": len(selected),
        "filters": config["selection"],
        "task_ids": [r["task_id"] for r in selected],
        "prs": metadata,
        "composition": _composition(metadata),
    }


def _composition(metadata: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Audit counts checked against the spec's known-good numbers."""
    md = list(metadata)
    def counts(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for m in md:
            out[str(m[key])] = out.get(str(m[key]), 0) + 1
        return dict(sorted(out.items()))
    return {
        "n": len(md),
        "difficulty": counts("difficulty"),
        "language": counts("language"),
        "has_requested_changes": counts("has_requested_changes"),
        "n_repos": len({m["repo"] for m in md}),
        "n_short_desc": sum(1 for m in md if m["short_desc"]),
    }
