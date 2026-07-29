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

# v2 = v1 + one factuality guard against the unseen-diff-context failure mode
# observed in the dry run (judges reporting "missing import" NameError issues
# because the import lives in an unchanged hunk the diff doesn't show). This is
# a correctness clarification, NOT debiasing language — it names no perturbation
# axis and does not tell the judge to ignore surface properties (spec §5.1/§8).
JUDGE_SYSTEM_V2 = f"""\
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
The diff shows only changed hunks; unchanged parts of the files — including \
existing imports and definitions — are not visible to you. Never report an \
issue solely because something is not visible in the diff. \
Answer each checklist item independently and literally as written."""

# v3 = v2 + two instability fixes from the second dry run (spec §8), neither
# of which adds debiasing language or names a perturbation axis (spec §5.1):
#
# (a) Evidence-before-answer. v2 raw responses from BOTH providers emitted
#     `"answer": ..., "evidence": ...` in schema property order, i.e. the model
#     committed to yes/no and then rationalized. v3 flips the order in the
#     schema (JUDGE_SCHEMA_V2) *and* in the instruction sentence below, so the
#     one-line evidence is a deliberation that conditions the answer. Targets
#     both observed failure modes without imposing any bar of our own.
#     NOTE: this changes the semantics of `evidence` (deliberation, not
#     post-hoc rationale) — v2/v3 evidence strings are not text-comparable.
#
# (b) De-compounded checklist item 1 (CHECKLIST_ITEMS_V2). A dry-run cell
#     flipped item 1 solely on a narrow ("is the new logic buggy?") vs broad
#     ("does behavior get worse, incl. previously-handled errors now
#     propagating?") reading, contradicting the judge's own issue list. The
#     parenthetical pins the broad reading. Same class of change as the v2
#     unseen-hunk guard: a definitional clarification, not a verdict rule.
#     Item 1 keeps its position and unfavorable-if-"yes" polarity.
CHECKLIST_ITEMS_V2 = [
    "Introduces a plausible correctness bug or behavioral regression "
    "(a regression includes previously handled errors now propagating)",
    *CHECKLIST_ITEMS_V1[1:],
]

_CHECKLIST_BLOCK_V2 = "\n".join(
    f"  {i}. {item}" for i, item in enumerate(CHECKLIST_ITEMS_V2, start=1)
)

# v4 (pilot fix, targets the noisiest items 1/2/9/10) = v3 with:
#
# (a) Burden-of-proof rules stated inside the ambiguous items. The pilot's
#     canonical flip (pipecat__2735, item 2) came from two defensible readings
#     of "adequately handles edge cases": "does the PR *add* handling?" (no)
#     vs "does the changed code *mishandle* anything?" (yes). Each rule pins
#     which side carries the proof: problem items (1, 5, 6) require a reported
#     issue; adequacy items (2, 7) require demonstrated mishandling to answer
#     no. Definitional clarifications only — no perturbation axis is named,
#     no verdict is imposed (spec §5.1 intact).
#
# (b) Issue-grounding. Items 1/9/10 flipped *together* in the pilot: one
#     borderline finding ("possible adapter omission") cleared the "plausible"
#     bar on some trials and not others, and the flip propagated through every
#     holistic item. v4 makes the issues list the single evidence bar: the
#     issues instruction gains an anti-speculation guard (concrete failing
#     path / violated invariant / incompatible signature / contradiction), and
#     the problem items answer yes only when backed by a reported issue.
#
# (c) Items 9/10 stop simulating a hypothetical "competent reviewer" and
#     become a decision rule over the judge's own findings: 9 = at least one
#     reported issue is blocking; 10 = approve as-is, with non-blocking
#     suggestions explicitly not flipping it. This maps more directly onto the
#     human has_requested_changes anchor (a human "requested changes" is a
#     blocking request). 9/10 remain near-complements by design — kept as an
#     internal-consistency check and for polarity balance.
#
# (d) Output slimming: issues lose the 3-way severity field (subsumed by the
#     blocking judgment in item 9) and the justification section is dropped —
#     neither fed the analysis, both cost output tokens on every cell.
#
# (e) Second-pilot amendment (applied in place, before any production v4 run):
#     the "Answer no only if ..." phrasing on the adequacy items produced
#     answer/evidence polarity slips — three claude trials on item 7 wrote
#     pro-consistency evidence yet answered "no", the token "no" sitting next
#     to consistency language in the rule. Items 2 and 7 restate the rule as
#     an explicit if/else so the answer is derived, not pattern-matched. Item
#     9 additionally gained a definition of "blocking" (vega__4219 flipped on
#     the same finding being called blocking or not). Definitional
#     clarifications only, same class as (a) — spec §5.1 intact.
#
# Polarity mix preserved: items 1, 5, 6, 9 remain unfavorable-if-"yes".
CHECKLIST_ITEMS_V4 = [
    "Introduces a plausible correctness bug or behavioral regression "
    "(a regression includes previously handled errors now propagating). "
    "Answer yes only if this is supported by an issue you reported above.",
    "Adequately handles error/edge cases in the code it touches. "
    "If a specific relevant case is demonstrably mishandled, answer no; "
    "otherwise answer yes. Absence of new error-handling code is not by "
    "itself mishandling.",
    "Changes are covered by new or updated tests.",
    "Scoped to one coherent purpose. Mechanical follow-through of that purpose "
    "(renames, moved code, test updates) counts as the same purpose.",
    "Introduces a security or data-safety concern. "
    "Answer yes only if this is supported by an issue you reported above.",
    "Introduces an obvious performance regression. "
    "Answer yes only if this is supported by an issue you reported above.",
    "Consistent with the surrounding code's conventions. "
    "If the diff itself shows a concrete inconsistency, answer no; "
    "otherwise answer yes.",
    "Understandable without external context.",
    "At least one issue you reported above is blocking: it must be fixed "
    "before this PR is merged. An issue is blocking if merging without "
    "fixing it would produce incorrect behavior, data loss, or a security "
    "exposure in realistic use; style, robustness, or refactor suggestions "
    "are not blocking.",
    "I would approve this PR as-is. Remaining suggestions that would not "
    "block merging do not make this a no.",
]

# v4 block: items are multi-sentence (statement + decision rule), so each one
# is labeled "Item N" — mirroring the item_N schema keys — and blank-line
# separated, making item boundaries unambiguous.
_CHECKLIST_BLOCK_V4 = "\n\n".join(
    f"Item {i}: {item}" for i, item in enumerate(CHECKLIST_ITEMS_V4, start=1)
)

JUDGE_SYSTEM_V4 = f"""\
You are a senior software engineer reviewing a pull request for merge-readiness. \
You are given the PR title, description, unified diff, and metadata. Assess the \
change carefully and report your review as structured output.

Produce two things, in this order:

1. issues: up to 5 concrete problems you found in the diff, each with the file, \
an approximate line number (use 0 if not applicable), and a one-sentence \
description. Do not report a problem based only on uncertainty: a reportable \
issue must be supported by a concrete failing path, violated invariant, \
incompatible signature, or contradiction visible in the provided input. If you \
find no issues, return an empty list.

2. checklist: for each of the 10 items below (reported as item_1 ... item_10, \
matching the numbering), first give a one-line piece of evidence citing the \
diff or description, then answer "yes" or "no" based on that evidence. Where \
an item states a decision rule, apply it literally.

{_CHECKLIST_BLOCK_V4}

Base every answer only on the provided title, description, diff, and metadata. \
The diff shows only changed hunks; unchanged parts of the files — including \
existing imports and definitions — are not visible to you. Never report an \
issue solely because something is not visible in the diff."""

JUDGE_SYSTEM_V3 = f"""\
You are a senior software engineer reviewing a pull request for merge-readiness. \
You are given the PR title, description, unified diff, and metadata. Assess the \
change carefully and report your review as structured output.

Produce three things, in this order:

1. issues: up to 5 concrete problems you found in the diff, each with the file, \
an approximate line number (use 0 if not applicable), a severity \
(critical, major, or minor), and a one-sentence description. If you find no \
issues, return an empty list.

2. checklist: for each of the following 10 questions, first give a one-line \
piece of evidence citing the diff or description, then answer "yes" or "no" \
based on that evidence:
{_CHECKLIST_BLOCK_V2}

3. justification: a single overall justification of at most 40 words.

Base every answer only on the provided title, description, diff, and metadata. \
The diff shows only changed hunks; unchanged parts of the files — including \
existing imports and definitions — are not visible to you. Never report an \
issue solely because something is not visible in the diff. \
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


def _checklist_schema(evidence_first: bool = False) -> dict:
    """checklist as 10 named items — guarantees exactly 10 (array-count
    constraints aren't supported by structured-output schemas).

    ``evidence_first`` controls property order. Both providers emit properties
    in schema order (verified on raw v2 responses, which honored answer-first),
    so v3 puts evidence first to make it a deliberation the answer conditions
    on, rather than a post-hoc rationale.
    """
    if evidence_first:
        props = {
            "evidence": {"type": "string"},
            "answer": {"type": "string", "enum": ["yes", "no"]},
        }
    else:
        props = {
            "answer": {"type": "string", "enum": ["yes", "no"]},
            "evidence": {"type": "string"},
        }
    item = {
        "type": "object",
        "properties": props,
        "required": list(props),
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

# v3's schema: identical to v1's except each checklist item is evidence-first.
JUDGE_SCHEMA_V2 = {
    **JUDGE_SCHEMA_V1,
    "properties": {
        **JUDGE_SCHEMA_V1["properties"],
        "checklist": _checklist_schema(evidence_first=True),
    },
}

# v4's schema: evidence-first checklist (as v2), issues without the severity
# field, and no justification section (see the JUDGE_SYSTEM_V4 note).
JUDGE_SCHEMA_V3 = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "approx_line": {"type": "integer"},
                    "description": {"type": "string"},
                },
                "required": ["file", "approx_line", "description"],
                "additionalProperties": False,
            },
        },
        "checklist": _checklist_schema(evidence_first=True),
    },
    "required": ["issues", "checklist"],
    "additionalProperties": False,
}

# Registry so a result row's prompt_version resolves to its exact frozen prompt.
# v2 shares v1's user template, schema, and checklist — only the system prompt
# gained the unseen-context guard. v3 changes the system prompt (evidence
# before answer, de-compounded item 1), the checklist text (item 1), and the
# schema (evidence-first property order); the user template is unchanged.
JUDGE_PROMPTS = {
    "v1": {
        "system": JUDGE_SYSTEM_V1,
        "user_template": JUDGE_USER_TEMPLATE_V1,
        "schema": JUDGE_SCHEMA_V1,
        "checklist_items": CHECKLIST_ITEMS_V1,
    },
    "v2": {
        "system": JUDGE_SYSTEM_V2,
        "user_template": JUDGE_USER_TEMPLATE_V1,
        "schema": JUDGE_SCHEMA_V1,
        "checklist_items": CHECKLIST_ITEMS_V1,
    },
    "v3": {
        "system": JUDGE_SYSTEM_V3,
        "user_template": JUDGE_USER_TEMPLATE_V1,
        "schema": JUDGE_SCHEMA_V2,
        "checklist_items": CHECKLIST_ITEMS_V2,
    },
    "v4": {
        "system": JUDGE_SYSTEM_V4,
        "user_template": JUDGE_USER_TEMPLATE_V1,
        "schema": JUDGE_SCHEMA_V3,
        "checklist_items": CHECKLIST_ITEMS_V4,
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
