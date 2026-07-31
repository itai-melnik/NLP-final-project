"""Unit tests for the Tier-B matcher's pure logic (spec 2026-07-30 §5).

Covers canonicalization/match_key stability, request building (dedupe,
zero-issue rows skipped), pairwise expansion + prompt rendering, and the
aggregation of pair answers back into per-issue verdicts.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge import matching as M  # noqa: E402

ISSUES = [
    {"file": "src/a.py", "approx_line": 10, "description": "off-by-one in loop", "severity": "major"},
    {"file": "src/b.py", "approx_line": 0, "description": "missing test", "severity": "minor"},
]
COMMENTS = [
    {"comment_id": "c_1", "file": "src/a.py", "line": 12, "body": "loop bound looks wrong"},
    {"comment_id": "c_2", "file": "src/c.py", "line": 3, "body": "typo in docstring"},
]


def _row(task="pr_a", judge="claude", variant="baseline", trial=1, issues=ISSUES):
    return {"task_id": task, "judge": judge, "variant": variant, "trial": trial,
            "issues": issues}


def _answer(match, confidence=0.9, reasoning="because"):
    return {"match": match, "confidence": confidence, "reasoning": reasoning}


def test_match_key_stable_and_ignores_extraneous_fields():
    k1 = M.match_key("pr_a", ISSUES)
    reordered_fields = [dict(reversed(list(i.items()))) for i in ISSUES]
    assert M.match_key("pr_a", reordered_fields) == k1  # canonical over key order
    extra = [{**ISSUES[0], "severity": "critical"}, ISSUES[1]]
    assert M.match_key("pr_a", extra) == k1  # only file/approx_line/description matter
    assert M.match_key("pr_b", ISSUES) != k1  # task_id is part of the key


def test_build_requests_dedupes_and_skips_empty():
    rows = [
        _row(trial=1), _row(trial=2),          # identical lists -> one request
        _row(trial=3, issues=[]),              # empty -> no request
        _row(judge="gpt", issues=[ISSUES[0]]),  # distinct list -> second request
    ]
    reqs = M.build_requests(rows, {"pr_a": COMMENTS})
    assert len(reqs) == 2
    keys = {r["match_key"] for r in reqs}
    assert M.match_key("pr_a", ISSUES) in keys


def test_build_pairs_is_issue_by_comment_cross_product():
    req = M.build_requests([_row()], {"pr_a": COMMENTS})[0]
    pairs = M.build_pairs(req)
    assert len(pairs) == 4  # 2 issues x 2 comments
    assert {(p["issue_idx"], p["comment_id"]) for p in pairs} == {
        (0, "c_1"), (0, "c_2"), (1, "c_1"), (1, "c_2")}
    assert len({p["pair_key"] for p in pairs}) == 4  # keys are distinct


def test_build_pairs_empty_when_pr_has_no_located_comments():
    req = M.build_requests([_row()], {"pr_a": []})[0]
    assert M.build_pairs(req) == []


def test_pair_prompt_renders_exactly_one_comment_and_one_issue():
    req = M.build_requests([_row()], {"pr_a": COMMENTS})[0]
    pair = next(p for p in M.build_pairs(req) if (p["issue_idx"], p["comment_id"]) == (0, "c_1"))
    sys_prompt = pair["system"]
    assert "loop bound looks wrong" in sys_prompt
    assert "off-by-one in loop" in sys_prompt
    assert "src/a.py:12" in sys_prompt and "src/a.py:10" in sys_prompt
    assert "typo in docstring" not in sys_prompt  # the other comment is absent
    assert "missing test" not in sys_prompt       # the other issue is absent
    assert "{human_comment}" not in sys_prompt    # placeholders were filled
    assert '{"reasoning"' in sys_prompt           # escaped JSON example survives


def test_sanitize_pair_answer_requires_boolean_match():
    assert M.sanitize_pair_answer(None) is None
    assert M.sanitize_pair_answer({"confidence": 0.9}) is None
    assert M.sanitize_pair_answer({"match": "yes"}) is None
    ans = M.sanitize_pair_answer({"match": True, "confidence": 1.7, "reasoning": None})
    assert ans == {"match": True, "confidence": 1.0, "reasoning": ""}  # clamped


def test_verdicts_from_pairs_picks_highest_confidence_match():
    pairs = [
        {"issue_idx": 0, "comment_id": "c_1", "answer": _answer(True, 0.6)},
        {"issue_idx": 0, "comment_id": "c_2", "answer": _answer(True, 0.9)},
        {"issue_idx": 1, "comment_id": "c_1", "answer": _answer(False)},
        {"issue_idx": 1, "comment_id": "c_2", "answer": _answer(False)},
    ]
    verdicts, dropped = M.verdicts_from_pairs(pairs, n_issues=2, comment_ids={"c_1", "c_2"})
    assert dropped == 0
    assert verdicts == [{"issue_idx": 0, "comment_id": "c_2"},
                        {"issue_idx": 1, "comment_id": None}]


def test_verdicts_from_pairs_drops_invalid_and_failed_pairs():
    pairs = [
        {"issue_idx": 0, "comment_id": "c_1", "answer": _answer(True)},
        {"issue_idx": 5, "comment_id": "c_1", "answer": _answer(True)},   # out of range
        {"issue_idx": 1, "comment_id": "c_9", "answer": _answer(True)},   # unknown comment
        {"issue_idx": 1, "comment_id": "c_2", "answer": None},            # failed call
    ]
    verdicts, dropped = M.verdicts_from_pairs(pairs, n_issues=2, comment_ids={"c_1", "c_2"})
    assert dropped == 3
    assert verdicts == [{"issue_idx": 0, "comment_id": "c_1"},
                        {"issue_idx": 1, "comment_id": None}]


def test_verdicts_cover_every_issue_even_with_no_pairs():
    verdicts, dropped = M.verdicts_from_pairs([], n_issues=3, comment_ids=set())
    assert dropped == 0
    assert [v["comment_id"] for v in verdicts] == [None, None, None]


def test_sanitize_verdicts_drops_invalid_entries():
    verdicts = [
        {"issue_idx": 0, "comment_id": "c_1"},   # valid match
        {"issue_idx": 1, "comment_id": None},  # valid no-match
        {"issue_idx": 5, "comment_id": "c_1"},   # out-of-range idx -> dropped
        {"issue_idx": 0, "comment_id": "c_9"},   # unknown comment -> dropped
    ]
    clean, n_dropped = M.sanitize_verdicts(verdicts, n_issues=2, comment_ids={"c_1", "c_2"})
    assert n_dropped == 2
    assert {(v["issue_idx"], v["comment_id"]) for v in clean} == {(0, "c_1"), (1, None)}


def test_matched_comment_ids_per_trial():
    clean = [{"issue_idx": 0, "comment_id": "c_1"}, {"issue_idx": 1, "comment_id": None}]
    assert M.matched_comment_ids(clean) == {"c_1"}
