# Semantic Issue Matching (Tier B) — Design

**Date:** 2026-07-30
**Status:** Approved design (v1)
**Context:** Replaces the weak `has_requested_changes` validity anchor (only 4/30
positives in the v2 pool) with issue-level validity: judge-reported issues matched
against human review comments. Complements the location-based Tier A metrics
(`issue_recall_precision`, analysis.py) already implemented.

## 1. What is measured

Unit of ground truth: the **located human review comment** (file + line/hunk +
body) from `annotations/<task_id>_human.json`. All located comments are used,
including the 11 gemini-code-assist bot comments (user decision 2026-07-30;
disclosed in the paper as a data note). 77 units across the 30 v2 PRs.

**Pre-registered metric decisions (declared before any matcher output existed):**

1. **Recall@5 is the primary validity metric.** The judge prompt caps issues at
   5; only 3/30 PRs have >5 located comments (oracle ceiling 0.948, reported
   alongside). Rationale: for a deployed judge, missed true issues are the
   costly, silent error; false positives are filtered by a human glance.
2. **Precision** (fraction of judge issues matching some human comment) is
   reported as context; **F2** (recall weighted 2×) is the single-number summary
   where one is needed.
3. **Δrecall per axis vs baseline** (paired within PR, trial-averaged — same
   convention as Δaggregate) is the perturbation-mechanism metric.
4. **Empty-trial convention:** a trial with zero reported issues contributes
   "matched nothing" to recall, contributes nothing to precision, and the
   empty-trial rate per judge is reported as its own column.
5. Trial combination: per human comment, match propensity = fraction of the
   cell's 3 trials in which ≥1 issue matched it; micro-averaged over comments.
   Precision pools issues across trials. Identical to Tier A conventions.

## 2. Matcher stage (new pipeline stage 03)

- **Task:** binary same-issue matching. A judge issue and a human comment match
  iff they describe the same underlying problem, regardless of phrasing or
  exact line number. Different problems at the same location do NOT match.
- **Requests:** one per unique `(task_id, canonical issue list)` — content-hash
  (`match_key` = sha256 of task_id + canonicalized issues). 834 unique of 838
  rows-with-issues in results_v2 (dedupe is a cheap safety, not a real saver).
  Rows with zero issues generate no request.
- **Model:** pilot on `claude-haiku-4-5`; if the human spot-check passes, full
  run on Haiku; otherwise escalate the pilot to `claude-opus-5` (user decision).
  Anthropic structured outputs via the existing `AnthropicJudge` client;
  temperature 0; full run through `AnthropicBatchClient` (Message Batches).
- **Prompt:** frozen as `matcher-v1` in `prompts.py`: system prompt with the
  matching criterion + JSON schema `{verdicts: [{issue_idx, comment_id|null}]}`;
  user message carries the PR title, the human comments (comment_id, file,
  line, body) and judge issues (idx, file, approx_line, description).
- **Artifact:** `artifacts/matching_v2.jsonl`, one row per unique request:
  `match_key`, `task_id`, `judge`, `matcher_model`, `matcher_model_version`,
  `matcher_prompt_version`, `verdicts`, `raw_text`, token counts, timestamp.
  Append-only, resumable by `match_key` (same discipline as stage 2). Frozen
  after the full run.
- **Pilot mode:** `scripts/03_match_issues.py --pilot` — deterministic
  stratified sample of ~15 unique requests (both judges; mix of 1-issue and
  multi-issue rows), direct (non-batch) API calls, writes
  `artifacts/matching_pilot.jsonl` + human-readable
  `artifacts/spotcheck_matching_pilot.md` for manual verification. The full
  run is gated on explicit user approval of the spot-check.

## 3. Analysis integration

- `semantic_recall_precision(df, matching_rows, units_by_task)` in
  `analysis.py` (TDD): joins each results row to its matcher verdicts via
  `match_key`; outputs the same shape as Tier A (`judge, variant, axis,
  recall, precision, n_human_units, n_judge_issues`) plus `f2` and
  `empty_trial_rate`, and a Δ-vs-baseline table per axis.
- Notebook §7 becomes the validity centerpiece: Tier B (semantic) headline,
  Tier A (location) as the assumption-free lower bound, item-9 κ demoted to a
  footnote. The notebook never calls an API — it reads `matching_v2.jsonl`.

## 4. Disclosures added to the paper

- Matcher is Claude-family (Haiku) while one judge is Claude-family
  (claude-sonnet-5): different model, and the pilot spot-check is the human
  audit; both stated.
- Bot comments retained in ground truth (11/77 from gemini-code-assist,
  6 PRs; 2 PRs have only bot comments).
- Recall is recall@5 with oracle ceiling 0.948.

## 5. Error handling & testing

- Matcher schema validated at the SDK layer (structured outputs); rows whose
  verdicts fail validation are recorded with `parsed=None` and re-tried on
  resume, mirroring stage 2.
- Verdict sanity: `issue_idx` must be in range; `comment_id` must be one of
  the PR's comment ids — invalid entries dropped and counted.
- Pure logic (canonicalization, match_key, request building, verdict
  application) lives in `src/prjudge/matching.py`, unit-tested
  (tests/test_matching.py) before implementation, per TDD.
