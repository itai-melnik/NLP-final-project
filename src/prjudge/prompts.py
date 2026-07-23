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
