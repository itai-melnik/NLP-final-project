"""Stage 1 — the 9 perturbation constructors + per-axis invariance checks (spec §4).

Each constructor takes the baseline *judge-input fields* of one selected PR and
returns a perturbed copy plus construction metadata. Deterministic variants are
pure functions of the input; the three verbosity variants call a construction
model (pinned, separate from the judges) and are cached so re-runs are
byte-identical unless explicitly regenerated.

Every axis has an invariance check (§4.2). The build script runs all checks and
refuses to freeze if any *blocking* check fails.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import Config
from .data import DiffSection, split_diff_sections
from .prompts import build_rewrite_messages

# Canonical variant order (mirrors config.variants.ids).
VARIANT_IDS = [
    "baseline",
    "verb_terse",
    "verb_pad2x",
    "verb_pad4x",
    "repo_masked",
    "origin_claude",
    "origin_gpt",
    "order_rev",
    "placebo",
]
VERBOSITY_VARIANTS = ("verb_terse", "verb_pad2x", "verb_pad4x")

# Axis label per variant (for reporting / analysis grouping).
VARIANT_AXIS = {
    "baseline": "baseline",
    "verb_terse": "verbosity",
    "verb_pad2x": "verbosity",
    "verb_pad4x": "verbosity",
    "repo_masked": "prestige",
    "origin_claude": "origin",
    "origin_gpt": "origin",
    "order_rev": "position",
    "placebo": "placebo",
}


# ---------------------------------------------------------------------------
# Judge-input fields
# ---------------------------------------------------------------------------

@dataclass
class JudgeInput:
    """The perturbable, judge-visible fields for one (task_id, variant)."""
    task_id: str
    variant: str
    title: str
    description: str
    diff_patch: str
    repo: str
    pr_number: int | str
    merged_at: str
    language: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "variant": self.variant,
            "title": self.title,
            "description": self.description,
            "diff_patch": self.diff_patch,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "merged_at": self.merged_at,
            "language": self.language,
        }


def base_fields(rec: dict[str, Any]) -> JudgeInput:
    """Extract the verbatim baseline judge input from a selected PR record."""
    return JudgeInput(
        task_id=rec["task_id"],
        variant="baseline",
        title=rec["title"],
        description=(rec.get("description") or "").strip(),
        diff_patch=rec.get("diff_patch") or "",
        repo=rec["repo"],
        pr_number=rec["pr_number"],
        merged_at=rec.get("merged_at") or "",
        language=rec.get("language"),
    )


def task_seed(config: Config, task_id: str) -> int:
    """Deterministic per-task seed derived from (master seed, task_id)."""
    h = hashlib.sha256(f"{config['seed']}:{task_id}".encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def word_count(text: str) -> int:
    """Whitespace word count — the unit the verbosity ratios are defined in (§4.1)."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Deterministic constructors
# ---------------------------------------------------------------------------

def _copy(base: JudgeInput, variant: str) -> JudgeInput:
    return JudgeInput(
        task_id=base.task_id, variant=variant, title=base.title,
        description=base.description, diff_patch=base.diff_patch, repo=base.repo,
        pr_number=base.pr_number, merged_at=base.merged_at, language=base.language,
    )


def build_baseline(base: JudgeInput, config: Config) -> tuple[JudgeInput, dict]:
    return _copy(base, "baseline"), {"deterministic": True}


def _repo_tokens(repo: str) -> tuple[str, str]:
    """Split 'org/name' into (org, name); tolerate a bare name."""
    if "/" in repo:
        org, name = repo.split("/", 1)
    else:
        org, name = "", repo
    return org, name


def mask_repo_text(text: str, org: str, name: str, token: str) -> str:
    """Scrub org/name from free text (metadata line or description).

    Replaces the full ``org/name`` slug, then the org and name tokens
    individually (case-insensitive, word-boundary), with the mask token /
    its halves. Cannot reach repo identity inside the diff (imports, paths) —
    that is the documented lower-bound limitation (§4.3).
    """
    mask_org, mask_name = (token.split("/", 1) + [token])[:2] if "/" in token else (token, token)
    out = text
    if org and name:
        out = re.sub(re.escape(f"{org}/{name}"), token, out, flags=re.IGNORECASE)
    if name:
        out = re.sub(rf"\b{re.escape(name)}\b", mask_name, out, flags=re.IGNORECASE)
    if org:
        out = re.sub(rf"\b{re.escape(org)}\b", mask_org, out, flags=re.IGNORECASE)
    return out


def build_repo_masked(base: JudgeInput, config: Config) -> tuple[JudgeInput, dict]:
    token = config["variants"]["repo_mask_token"]
    org, name = _repo_tokens(base.repo)
    v = _copy(base, "repo_masked")
    v.repo = token
    v.description = mask_repo_text(base.description, org, name, token)
    return v, {"deterministic": True, "masked_org": org, "masked_name": name}


def build_origin(base: JudgeInput, config: Config, family: str) -> tuple[JudgeInput, dict]:
    """Append an authorship trailer to the description (realistic PR-tail placement).

    §3 filter 4 screens out PRs that already carry such a trailer, so the
    baseline is "no authorship claim"; this axis adds exactly one.
    """
    key = "origin_claude_trailer" if family == "claude" else "origin_gpt_trailer"
    trailer = config["variants"][key]
    v = _copy(base, f"origin_{family}")
    v.description = f"{base.description}\n\n{trailer}"
    return v, {"deterministic": True, "trailer": trailer}


def build_order_rev(base: JudgeInput, config: Config) -> tuple[JudgeInput, dict]:
    """Reverse the per-file diff sections; diff content is otherwise untouched."""
    sections = split_diff_sections(base.diff_patch)
    reversed_sections = list(reversed(sections))
    v = _copy(base, "order_rev")
    v.diff_patch = "".join(s.text for s in reversed_sections)
    return v, {
        "deterministic": True,
        "seed": task_seed(config, base.task_id),   # provenance; reversal itself is fixed
        "n_sections": len(sections),
        "order_before": [s.path for s in sections],
        "order_after": [s.path for s in reversed_sections],
    }


def build_placebo(base: JudgeInput, config: Config) -> tuple[JudgeInput, dict]:
    v = _copy(base, "placebo")
    v.pr_number = config["variants"]["placebo_pr_number"]
    v.merged_at = config["variants"]["placebo_date"]
    return v, {"deterministic": True}


# ---------------------------------------------------------------------------
# Verbosity constructors (LLM-assisted, cached)
# ---------------------------------------------------------------------------

def build_verbosity(base: JudgeInput, variant: str, rewrite_text: str) -> tuple[JudgeInput, dict]:
    """Wrap a (cached or freshly generated) rewrite into a JudgeInput."""
    v = _copy(base, variant)
    v.description = rewrite_text.strip()
    return v, {"deterministic": False}


def rewrite_cache_key(task_id: str, variant: str, prompt_version: str, model: str) -> str:
    return hashlib.sha256(
        f"{task_id}|{variant}|{prompt_version}|{model}".encode("utf-8")
    ).hexdigest()


def generate_rewrite(
    description: str, variant: str, config: Config, *, mock: bool = False
) -> str:
    """Produce a verbosity rewrite via the construction model (or a mock).

    Mock mode fabricates a length-adjusted rewrite deterministically (no API,
    no key) purely to exercise the pipeline; it is NOT semantically faithful and
    must never feed a real run.
    """
    target = config["variants"]["verbosity_targets"][variant]
    if mock:
        return _mock_rewrite(description, target)

    cm = config["variants"]["construction_model"]
    if cm["provider"] == "claude-code":
        # Rewrites for this provider are authored interactively via the
        # rewrite-variants skill and pre-populated into rewrites_cache.json;
        # a cache miss must surface as a work-queue item, never an API call.
        raise ValueError(
            "construction provider is 'claude-code': rewrites must be pre-populated "
            "in rewrites_cache.json via the rewrite-variants skill (see "
            ".claude/skills/rewrite-variants/SKILL.md); run scripts/01_build_variants.py "
            "to (re)generate the pending work queue"
        )
    system, user = build_rewrite_messages(description, variant, target, version="v1")
    if cm["provider"] != "anthropic":
        raise ValueError(f"unsupported construction provider: {cm['provider']}")
    # Lazy import so the package loads without the SDK / a key present.
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=cm["model"],
        max_tokens=cm["max_tokens"],
        temperature=cm["temperature"],
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()


def _mock_rewrite(description: str, target_ratio: float) -> str:
    """Deterministic length-adjusted stand-in for a real rewrite (testing only)."""
    words = description.split()
    n = len(words)
    target = max(1, round(n * target_ratio))
    if target <= n:
        return " ".join(words[:target])
    # Pad by cycling the original words (keeps it deterministic and in-band).
    out = list(words)
    i = 0
    while len(out) < target:
        out.append(words[i % n])
        i += 1
    return " ".join(out)


# ---------------------------------------------------------------------------
# Invariance checks (spec §4.2)
# ---------------------------------------------------------------------------

@dataclass
class Check:
    name: str
    passed: bool
    blocking: bool
    detail: str = ""


def check_variant(
    variant: JudgeInput, baseline: JudgeInput, config: Config, *, meta: dict
) -> list[Check]:
    """Run the per-axis invariance checks for one variant against its baseline."""
    checks: list[Check] = []
    axis = VARIANT_AXIS[variant.variant]

    # -- diff invariance ---------------------------------------------------
    if variant.variant == "order_rev":
        base_sections = sorted(s.text for s in split_diff_sections(baseline.diff_patch))
        var_sections = sorted(s.text for s in split_diff_sections(variant.diff_patch))
        ok = base_sections == var_sections
        checks.append(Check(
            "diff_section_multiset_identical", ok, blocking=True,
            detail="" if ok else "reordered diff is not a pure permutation of baseline sections",
        ))
        # And confirm the order actually changed (unless a single-section diff).
        changed = variant.diff_patch != baseline.diff_patch or meta.get("n_sections", 0) <= 1
        checks.append(Check("diff_order_changed", changed, blocking=False,
                            detail="" if changed else "order identical to baseline"))
    else:
        ok = variant.diff_patch == baseline.diff_patch
        checks.append(Check("diff_byte_identical", ok, blocking=True,
                            detail="" if ok else "diff differs from baseline"))

    # -- description invariance -------------------------------------------
    if variant.variant == "baseline":
        pass
    elif variant.variant in VERBOSITY_VARIANTS:
        checks.append(_verbosity_ratio_check(variant, baseline, config, meta))
    elif variant.variant == "repo_masked":
        # Description must equal the pure name-substitution of the baseline, and
        # no residual org/name token may remain in the masked text/metadata.
        org, name = meta.get("masked_org", ""), meta.get("masked_name", "")
        token = config["variants"]["repo_mask_token"]
        redo = mask_repo_text(baseline.description, org, name, token)
        ok = variant.description == redo
        checks.append(Check("desc_name_substitution_only", ok, blocking=True,
                            detail="" if ok else "masked description is not a pure name substitution"))
        residual_desc = _has_token(variant.description, name) or _has_token(variant.description, org)
        residual_meta = _has_token(str(variant.repo), name) or _has_token(str(variant.repo), org)
        checks.append(Check("no_residual_repo_token", not (residual_desc or residual_meta),
                            blocking=False,
                            detail="repo/org token still present after masking" if (residual_desc or residual_meta) else ""))
    elif variant.variant in ("origin_claude", "origin_gpt"):
        # Description == baseline + "\n\n" + trailer; baseline is an exact prefix.
        trailer = meta.get("trailer", "")
        expected = f"{baseline.description}\n\n{trailer}"
        ok = variant.description == expected
        checks.append(Check("desc_baseline_plus_trailer_only", ok, blocking=True,
                            detail="" if ok else "description changed beyond the appended trailer"))
    elif variant.variant == "placebo":
        ok = variant.description == baseline.description
        checks.append(Check("desc_byte_identical", ok, blocking=True,
                            detail="" if ok else "description differs from baseline"))
        meta_changed = (str(variant.pr_number) != str(baseline.pr_number)
                        and variant.merged_at != baseline.merged_at)
        checks.append(Check("placebo_metadata_changed", meta_changed, blocking=False,
                            detail="" if meta_changed else "pr_number/date not changed"))

    return checks


def _verbosity_ratio_check(
    variant: JudgeInput, baseline: JudgeInput, config: Config, meta: dict
) -> Check:
    """Token-ratio band check; non-blocking for flagged short-description PRs (§3)
    and for pre-registered terse-infeasible PRs (config: variants.terse_waivers)."""
    target = config["variants"]["verbosity_targets"][variant.variant]
    tol = config["variants"]["verbosity_tolerance"]
    base_words = word_count(baseline.description)
    var_words = word_count(variant.description)
    ratio = var_words / base_words if base_words else float("nan")
    lo, hi = target * (1 - tol), target * (1 + tol)
    ok = lo <= ratio <= hi
    short = bool(meta.get("short_desc"))
    waived = (variant.variant == "verb_terse"
              and meta.get("task_id") in set(config["variants"].get("terse_waivers", [])))
    detail = f"ratio={ratio:.2f} target={target} band=[{lo:.2f},{hi:.2f}] words={var_words}/{base_words}"
    if short and not ok:
        detail += " (short_desc: exempt, non-blocking)"
    elif waived and not ok:
        detail += " (terse_waiver: exempt, non-blocking)"
    # Short-desc / waived PRs cannot hit the band under the invariance rules;
    # log but do not block freeze. Their terse cells are excluded from the
    # dose-response analysis (spec §4.2/§8).
    exempt = short or waived
    return Check("verbosity_token_ratio", ok or exempt, blocking=not exempt, detail=detail)


def _has_token(text: str, token: str) -> bool:
    if not token:
        return False
    return re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE) is not None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

# Deterministic constructor dispatch (verbosity handled separately).
DETERMINISTIC_BUILDERS: dict[str, Callable[[JudgeInput, Config], tuple[JudgeInput, dict]]] = {
    "baseline": build_baseline,
    "repo_masked": build_repo_masked,
    "origin_claude": lambda b, c: build_origin(b, c, "claude"),
    "origin_gpt": lambda b, c: build_origin(b, c, "gpt"),
    "order_rev": build_order_rev,
    "placebo": build_placebo,
}


@dataclass
class BuiltVariant:
    judge_input: JudgeInput
    construction: dict
    checks: list[Check] = field(default_factory=list)

    @property
    def blocking_failures(self) -> list[Check]:
        return [c for c in self.checks if c.blocking and not c.passed]
