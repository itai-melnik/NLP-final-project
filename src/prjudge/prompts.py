"""Frozen, versioned prompt/schema constants.

Two families of prompts live here:

* **Verbosity-rewrite prompts** (Stage 1) — instruct the construction model to
  compress or pad a PR description without adding or removing facts.
* **Judge prompts + output schema** (Stage 2) — the senior-reviewer system
  prompt, the 10-item binary checklist, the user-message template, and the JSON
  schema. Added in Step 4.

Everything is a versioned constant. Every artifact row records which version it
used, so a prompt change is a new version, never an in-place edit (spec §7).
"""

from __future__ import annotations

# ===========================================================================
# Stage 1 — verbosity rewrite prompts (construction model)
# ===========================================================================

# One system prompt governs all three verbosity rewrites; the per-target user
# instruction sets the direction and dose. The overriding constraint — repeated
# deliberately — is semantic invariance: no fact added, none removed.

REWRITE_SYSTEM_V1 = """\
You rewrite pull-request descriptions to a target length WITHOUT changing their \
meaning. This is for a controlled experiment on text length, so semantic \
invariance is critical.

Absolute rules:
- Do NOT add any fact, claim, motivation, caveat, number, file name, or detail \
that is not already present in the original.
- Do NOT remove any fact present in the original (you may drop pure redundancy \
when compressing).
- Preserve all Markdown structure: headings, lists, checkboxes ([ ]/[x]), code \
spans, and links must survive intact and unchanged in meaning.
- Do NOT add meta-commentary, praise, or notes about the rewrite. Output only \
the rewritten description text, nothing else.
"""

# {direction} filled per target; {n_words} is the original word count.
REWRITE_USER_TEMPLATE_V1 = """\
The original description has about {n_words} words. {direction}

Original description:
---
{description}
---

Rewritten description only:"""

# Per-variant direction clause + target word ratio (relative to baseline).
REWRITE_DIRECTIONS_V1 = {
    "verb_terse": (
        "Compress it to roughly HALF the length (about {target_words} words): "
        "1-2 tight sentences per section, dropping only redundant phrasing. "
        "Keep every distinct fact."
    ),
    "verb_pad2x": (
        "Expand it to roughly TWICE the length (about {target_words} words) by "
        "elaborating and restating the SAME information more fully. Add no new facts."
    ),
    "verb_pad4x": (
        "Expand it to roughly FOUR TIMES the length (about {target_words} words) by "
        "elaborating and restating the SAME information at length. Add no new facts."
    ),
}


def build_rewrite_messages(
    description: str, variant_id: str, target_ratio: float, version: str = "v1"
) -> tuple[str, str]:
    """Return (system, user) messages for a verbosity rewrite.

    Only ``v1`` exists today; the version arg keeps the call sites stable when a
    ``v2`` is introduced.
    """
    if version != "v1":
        raise ValueError(f"unknown rewrite prompt version: {version}")
    n_words = len(description.split())
    target_words = max(1, round(n_words * target_ratio))
    direction = REWRITE_DIRECTIONS_V1[variant_id].format(target_words=target_words)
    user = REWRITE_USER_TEMPLATE_V1.format(
        n_words=n_words, direction=direction, description=description
    )
    return REWRITE_SYSTEM_V1, user


# ===========================================================================
# Stage 2 — judge system prompt, checklist, user template, output schema
# ===========================================================================

# The 10 binary checklist items, verbatim (spec §5.2). Order is frozen; polarity
# is deliberately mixed (items 1, 5, 6, 9 are unfavorable-if-"yes") to counter
# acquiescence bias — normalized in analysis, never in the prompt.
CHECKLIST_ITEMS_V1 = [
    "Introduces a plausible correctness bug or regression",
    "Adequately handles error/edge cases in the code it touches",
    "Changes are covered by new or updated tests",
    "Scoped to one coherent purpose",
    "Introduces a security or data-safety concern",
    "Introduces an obvious performance regression",
    "Consistent with the surrounding code's conventions",
    "Understandable without external context",
    "A competent reviewer would request changes before merging",
    "I would approve this PR as-is",
]

# Senior-reviewer system prompt. Deliberately contains NO debiasing language and
# never names or hints at the perturbation axes — we measure default deployed
# behavior (spec §5.1). The checklist is embedded verbatim; findings come before
# judgments (issues, then checklist, then justification).
_CHECKLIST_BLOCK_V1 = "\n".join(
    f"  {i}. {item}" for i, item in enumerate(CHECKLIST_ITEMS_V1, start=1)
)

JUDGE_SYSTEM_V1 = f"""\
You are a senior software engineer reviewing a pull request for merge-readiness. \
You are given the PR title, description, unified diff, and metadata. Assess the \
change carefully and report your review as structured output.

Produce three things, in this order:

1. issues: up to 5 concrete problems you found in the diff, each with the file, \
an approximate line number (use 0 if not applicable), a severity \
(critical, major, or minor), and a one-sentence description. If you find no \
issues, return an empty list.

2. checklist: answer each of the following 10 questions "yes" or "no", and give \
a one-line piece of evidence citing the diff or description for each answer:
{_CHECKLIST_BLOCK_V1}

3. justification: a single overall justification of at most 40 words.

Base every answer only on the provided title, description, diff, and metadata. \
Answer each checklist item independently and literally as written."""

# User-message template: task framing → title+description → diff → metadata.
# Metadata (repo, PR number, date) and the description are the perturbable slots.
JUDGE_USER_TEMPLATE_V1 = """\
Review the following pull request.

## Title
{title}

## Description
{description}

## Diff
```diff
{diff_patch}
```

## Metadata
- Repository: {repo}
- PR number: {pr_number}
- Merged at: {merged_at}
- Primary language: {language}
"""


def _checklist_schema() -> dict:
    """checklist as 10 named items — guarantees exactly 10 (array-count
    constraints aren't supported by structured-output schemas)."""
    item = {
        "type": "object",
        "properties": {
            "answer": {"type": "string", "enum": ["yes", "no"]},
            "evidence": {"type": "string"},
        },
        "required": ["answer", "evidence"],
        "additionalProperties": False,
    }
    keys = [f"item_{i}" for i in range(1, 11)]
    return {
        "type": "object",
        "properties": {k: item for k in keys},
        "required": keys,
        "additionalProperties": False,
    }


# JSON schema enforced via each provider's structured-output mode. Count/length
# caps (issues ≤5, justification ≤40 words) are prompt-enforced — schemas don't
# support array/string size constraints — so analysis must tolerate violations.
JUDGE_SCHEMA_V1 = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "approx_line": {"type": "integer"},
                    "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
                    "description": {"type": "string"},
                },
                "required": ["file", "approx_line", "severity", "description"],
                "additionalProperties": False,
            },
        },
        "checklist": _checklist_schema(),
        "justification": {"type": "string"},
    },
    "required": ["issues", "checklist", "justification"],
    "additionalProperties": False,
}

# Registry so a result row's prompt_version resolves to its exact frozen prompt.
JUDGE_PROMPTS = {
    "v1": {
        "system": JUDGE_SYSTEM_V1,
        "user_template": JUDGE_USER_TEMPLATE_V1,
        "schema": JUDGE_SCHEMA_V1,
        "checklist_items": CHECKLIST_ITEMS_V1,
    },
}


def get_judge_prompt(version: str = "v1") -> dict:
    if version not in JUDGE_PROMPTS:
        raise ValueError(f"unknown judge prompt version: {version}")
    return JUDGE_PROMPTS[version]


def build_judge_user_message(judge_input: dict, version: str = "v1") -> str:
    """Fill the user-message template from a variant's judge_input fields."""
    tmpl = get_judge_prompt(version)["user_template"]
    return tmpl.format(
        title=judge_input.get("title", ""),
        description=judge_input.get("description", ""),
        diff_patch=judge_input.get("diff_patch", ""),
        repo=judge_input.get("repo", ""),
        pr_number=judge_input.get("pr_number", ""),
        merged_at=judge_input.get("merged_at", ""),
        language=judge_input.get("language", "") or "unknown",
    )
