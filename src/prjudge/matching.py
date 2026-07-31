"""Stage 3b — semantic issue matching (Tier B validity, spec 2026-07-30).

Pure logic for the matcher stage: canonical request keys, request building
(dedupe over identical issue lists, zero-issue rows skipped), pairwise
(comment x issue) prompt rendering, and aggregation of pair verdicts back to
one verdict per issue. The API-calling CLI lives in
``scripts/03_match_issues.py``; this module never calls a network.

Prompt v2 is *pairwise*: one call judges exactly one (human comment, judge
issue) pair and answers {reasoning, match, confidence}. Pair answers are
aggregated here into the spec's ``verdicts`` shape (one comment_id-or-null per
issue_idx), so the artifact and the downstream analysis contract are unchanged.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

MATCHER_PROMPT_VERSION = "matcher-v3"


MATCHER_SYSTEM_V1 = """\
You are evaluating LLM-as-a-judge for PR code reviews.
Determine if the candidate issue matches the human comment on the same PR.

Human Comment (expected issue):
{human_comment}

Candidate Issue (from the LLM-as-a-judge)
{candidate_issue}

Instructions:

- Determine if the candidate issue matches the human comment

- Be lenient. The question is "did the judge notice the same thing the reviewer
  was worried about?", not "did the judge explain or fix it the same way?"

- Accept semantic matches - different wording is fine if it's the same problem

- Accept partial and imprecise matches: it still counts if the candidate's
  explanation of the cause, its severity, or its suggested fix differ from the
  human's, if it covers only part of what the human raised, or if it describes
  the same underlying problem by a downstream symptom

- Accept it when the candidate is pointing in the right direction - it flagged
  the same code as problematic for a related reason - even when its diagnosis is
  wrong or its recommendation is the opposite of the human's. Recognizing the
  contested code is what counts

- Do NOT match on location alone. The same file or line paired with a clearly
  unrelated concern (a style nitpick vs. a crash, an import vs. an off-by-one)
  is not a match. If the human comment carries no substantive text, answer false

- Respond with ONLY a JSON object:

{{"reasoning": "brief explanation", "match": true/false, "confidence": 0.0-1.0}}"""

# The pair itself lives in the (formatted) system prompt above; the user turn
# only has to trigger the answer.
MATCHER_USER_V1 = "Do they match? Respond with ONLY the JSON object."


MATCHER_SCHEMA_V1: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "match": {"type": "boolean"},
        "confidence": {"type": "number"},
    },
    "required": ["reasoning", "match", "confidence"],
    "additionalProperties": False,
}

_CANON_FIELDS = ("file", "approx_line", "description")


def canonical_issues(issues: list[dict]) -> list[dict]:
    """Project each issue onto the fields that define its identity."""
    return [{k: i.get(k) for k in _CANON_FIELDS} for i in issues or []]


def match_key(task_id: str, issues: list[dict]) -> str:
    """Stable identity of one matcher request: task + canonical issue list."""
    canon = json.dumps(canonical_issues(issues), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(f"{task_id}|{canon}".encode("utf-8")).hexdigest()


def pair_key(mkey: str, issue_idx: int, comment_id: str) -> str:
    """Stable identity of one pairwise matcher call (for resume/dedupe)."""
    return hashlib.sha256(f"{mkey}|{issue_idx}|{comment_id}".encode("utf-8")).hexdigest()


def render_comment(comment: dict) -> str:
    """The human side of a pair, as shown to the matcher."""
    loc = f"{comment.get('file')}:{comment.get('line')}" if comment.get("file") else "(no location)"
    body = " ".join((comment.get("body") or "").split())
    return f"location: {loc}\n{body}"


def render_issue(issue: dict) -> str:
    """The judge side of a pair, as shown to the matcher."""
    loc = f"{issue.get('file')}:{issue.get('approx_line')}" if issue.get("file") else "(no location)"
    return f"location: {loc}\n{issue.get('description') or ''}"


def build_requests(rows: list[dict], comments_by_task: dict[str, list[dict]]) -> list[dict]:
    """Unique matcher requests from results rows.

    One request per unique (task_id, canonical issue list); rows with zero
    issues generate none. Each request carries the sample metadata needed to
    expand into pairs, write the artifact row, and render the spot-check.
    """
    seen: dict[str, dict] = {}
    for r in rows:
        issues = r.get("issues") or []
        if not issues:
            continue
        key = match_key(r["task_id"], issues)
        if key in seen:
            continue
        comments = comments_by_task.get(r["task_id"], [])
        seen[key] = {
            "match_key": key,
            "task_id": r["task_id"],
            "judge": r["judge"],
            "issues": canonical_issues(issues),
            "n_issues": len(issues),
            "comments": comments,
            "comment_ids": [c["comment_id"] for c in comments],
        }
    return list(seen.values())


def build_pairs(req: dict) -> list[dict]:
    """Expand one request into its (issue, human comment) matcher calls.

    A request whose PR has no located comments yields no pairs — every issue is
    then an unmatched (precision-only) issue, recorded by ``verdicts_from_pairs``.
    """
    pairs = []
    for idx, issue in enumerate(req["issues"]):
        for comment in req["comments"]:
            cid = comment["comment_id"]
            pairs.append({
                "pair_key": pair_key(req["match_key"], idx, cid),
                "match_key": req["match_key"],
                "task_id": req["task_id"],
                "judge": req["judge"],
                "issue_idx": idx,
                "comment_id": cid,
                "system": MATCHER_SYSTEM_V1.format(
                    human_comment=render_comment(comment),
                    candidate_issue=render_issue(issue),
                ),
                "user": MATCHER_USER_V1,
            })
    return pairs


def sanitize_pair_answer(parsed: dict | None) -> dict | None:
    """Coerce one pair answer to {match: bool, confidence: float, reasoning: str}.

    Returns None when the answer is missing or has no usable ``match`` field —
    the caller counts those as failed pairs rather than as "no match".
    """
    if not isinstance(parsed, dict) or not isinstance(parsed.get("match"), bool):
        return None
    try:
        conf = float(parsed.get("confidence"))
    except (TypeError, ValueError):
        conf = 0.0
    conf = min(1.0, max(0.0, conf))
    return {"match": parsed["match"], "confidence": conf,
            "reasoning": str(parsed.get("reasoning") or "")}


def verdicts_from_pairs(pair_answers: list[dict], *, n_issues: int,
                        comment_ids: set) -> tuple[list[dict], int]:
    """Aggregate pair answers into one verdict per issue.

    Emits exactly one ``{issue_idx, comment_id}`` per issue: the matching
    comment with the highest confidence, or ``None`` when no pair matched.
    Pairs with an out-of-range index, an unknown comment_id, or a failed answer
    are dropped and counted.
    """
    best: dict[int, tuple[float, str]] = {}
    dropped = 0
    for p in pair_answers or []:
        idx, cid = p.get("issue_idx"), p.get("comment_id")
        if not isinstance(idx, int) or not (0 <= idx < n_issues) or cid not in comment_ids:
            dropped += 1
            continue
        ans = p.get("answer")
        if ans is None:
            dropped += 1
            continue
        if not ans["match"]:
            continue
        # Ties break on comment_id so the verdict is deterministic.
        cand = (ans["confidence"], cid)
        if idx not in best or cand > best[idx]:
            best[idx] = cand
    verdicts = [{"issue_idx": i, "comment_id": best[i][1] if i in best else None}
                for i in range(n_issues)]
    return verdicts, dropped


def sanitize_verdicts(verdicts: list[dict], *, n_issues: int,
                      comment_ids: set) -> tuple[list[dict], int]:
    """Drop verdicts with out-of-range issue_idx or unknown comment_id."""
    clean, dropped = [], 0
    for v in verdicts or []:
        idx, cid = v.get("issue_idx"), v.get("comment_id")
        if not isinstance(idx, int) or not (0 <= idx < n_issues):
            dropped += 1
            continue
        if cid is not None and cid not in comment_ids:
            dropped += 1
            continue
        clean.append({"issue_idx": idx, "comment_id": cid})
    return clean, dropped


def matched_comment_ids(verdicts: list[dict]) -> set:
    """Comment ids matched by >=1 issue in one trial's sanitized verdicts."""
    return {v["comment_id"] for v in verdicts if v["comment_id"] is not None}
