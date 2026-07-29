# Experimental Pipeline Design — Non-Semantic Sensitivity in LLM Judges of Pull Requests

**Date:** 2026-07-23
**Status:** Approved design (v1)
**Project:** "What Moves the Judge? Non-Semantic Sensitivity in LLM Judges of Pull Requests"

## 1. Research question and measurement logic

For an LLM judge evaluating pull requests, which non-semantic properties of the PR
most affect its evaluation? We hold the code change (diff) fixed, perturb exactly one
surface property at a time, and measure the shift in the judge's evaluation — a fixed
10-item binary review checklist (§5.2), aggregated to a 0–10 score in analysis —
against the same PR's unperturbed baseline. Because the comparison is
**within-PR**, defect status is automatically held constant; no buggy/clean binary
label is required.

**Admission criterion for a perturbation axis:** an ideal judge should be invariant
to it. Properties a rubric could legitimately reward (e.g., variable naming, added
context) are excluded by construction.

## 2. Data source (verified facts)

Source: local copy of **SWE-PRBench** (`swe-prbench/dataset/`), verified complete
2026-07-23:

- `prs.jsonl` — 350 records; all task_ids match 1:1 with `annotations/` and all three
  `contexts/` configs; all 100 `evals/eval_100.json` ids resolve.
- Relevant fields per record: `task_id`, `repo`, `pr_number`, `title`,
  **`description`** (full author-written PR body; median ~940 chars; 11/350 near-empty),
  `diff_patch` (full unified diff; median ~16k chars, p90 ~40k, max 13M),
  `difficulty` (Type1_Direct / Type2_Contextual / Type3_Latent),
  `has_requested_changes` (71/350 true), `language`, `human_review_comments`.
- The `severity` field is null in all records, and per-comment `severity` /
  `is_blocking` in the annotations are likewise null everywhere — ignore them.
  The **populated** human signals are: per-comment `requires_change` (510 true /
  1,674 comments), per-comment `file` + `line` + `diff_hunk` (issue locations),
  PR-level `has_requested_changes` (71/350) and `requested_change_count`.
- **No repo cloning and no external API calls are needed at any stage.** The diff and
  description are in the data. The pipeline is pure text-in/text-out over API judges.
- The frozen `contexts/config_*` prompts are **not** reused (they contain no
  description slot and a fixed template); we build our own template (§5).

**Ground-truth caveat (by design of SWE-PRBench):** every PR has ≥2 substantive human
review comments and all PRs were merged. There is no defect-free subset. Decision:
treat "seriousness of human-flagged issues" as a continuous/ordinal covariate
(annotation comment count/type + `has_requested_changes`), not a binary label.

## 3. Stage 0 — PR selection (one-time, frozen)

Selection pool: the 100 ids in `evals/eval_100.json` (the paper's curated,
difficulty-stratified evaluation split — a documented provenance for the item
set rather than an ad-hoc sample of our own).

Filters (all verified on the actual data):
1. `description` ≥ 20 chars after stripping (drops empty/boilerplate bodies).
2. `diff_patch` ≤ 30,000 chars (~7.5k tokens) so total judge input stays under a
   fixed budget and a few monster diffs don't dominate variance.
3. ≥ 2 file sections in the diff, with a **mix of test and non-test files** —
   the file-order axis (and its tests-position contrast) is then defined for
   every selected PR.
4. **AI/bot-authorship screen:** descriptions were screened for explicit
   disclosure of AI/bot authorship or embedded bot-review content (e.g., a PR
   description ending in "🤖 Generated with Claude Code", or an embedded Cursor
   Bugbot report); such PRs are dropped, since a pre-existing authorship
   disclosure contaminates the origin axis, whose baseline is defined as "no
   authorship claim." (One of these also had zero review comments — no ground
   truth.) See the limitation note below.

Result: **n = 40** — all eligible PRs are used; no random sampling step.
Verified composition: difficulty 12 Direct / 15 Contextual / 13 Latent;
25 distinct repos (max 4 per repo); languages 23 Py / 6 Go / 5 JS / 5 TS / 1 Java;
`has_requested_changes` 13 true / 27 false; judge input 524–8,347 est. tokens
(median ~2,500). Total calls: 40 × 9 × 2 × 3 = **2,160**.

**Test-file detection note (implementation).** Filter 3 requires a genuine
test/non-test mix. An earlier count of n = 41 was produced with a loose detector
that treated the substring `spec` anywhere in a filename as a test signal; this
false-positived on `spyder__24990`'s `.../kernelspec.py` (a config file, not a
test), admitting a PR with no real test file. We use principled test-file
detection instead (test/spec as a path *token* — directory or basename pattern,
not an incidental substring), which correctly excludes `spyder__24990`, giving
n = 40. This keeps the tests-position contrast (§6) well-defined for every
selected PR.

Four PRs have very short descriptions (< 150 chars), which compresses the
verbosity axis for them (terse ≈ baseline). They are kept (they are legitimate
real PRs) but flagged in the manifest; the verbosity analysis includes a
sensitivity check excluding them.

**Limitation (record in paper):** excluding explicitly AI-authored PRs is
necessary for a clean origin baseline but means the origin axis measures the
effect of the authorship *label* on human-authored code, not the judgment of
genuinely AI-authored PRs. (SWE-PRBench itself already filters out PRs with
heavy bot review activity, so the dataset skews human throughout.)

**Frozen artifact:** `selection_manifest_v1.json` (task_ids + filter parameters
+ short-description flags). Never modified after freeze.

## 4. Stage 1 — Variant construction (offline, frozen)

### 4.1 Variant matrix (9 variants per PR)

| # | Variant id | Axis | Construction | Deterministic? |
|---|-----------|------|--------------|----------------|
| 1 | `baseline` | — | original description verbatim, natural file order, real repo name, no authorship trailer | yes |
| 2 | `verb_terse` | verbosity | Claude Code rewrite (skill `cc-v1`, §4.5): compress description to 1–2 sentences, zero information removed beyond redundancy | no |
| 3 | `verb_pad2x` | verbosity | Claude Code rewrite (skill `cc-v1`, §4.5): ~2× word count, zero information added | no |
| 4 | `verb_pad4x` | verbosity | Claude Code rewrite (skill `cc-v1`, §4.5): ~4× word count, zero information added | no |
| 5 | `repo_masked` | prestige / memorization | script: replace repo name/org in metadata line and description with `project/repo`; diff untouched | yes |
| 6 | `origin_claude` | model-of-origin | script: append trailer `Co-Authored-By: Claude <noreply@anthropic.com>` | yes |
| 7 | `origin_gpt` | model-of-origin | script: append equivalent GPT-family trailer (Codex/Copilot style) | yes |
| 8 | `order_rev` | position | script: reverse the order of per-file diff sections (seeded per task_id) | yes |
| 9 | `placebo` | negative control | script: change PR number and date only; expected effect ≈ 0 | yes |

Verbosity is a **dose–response axis** (terse < baseline < 2× < 4×): a monotonic
score-vs-length trend is the target evidence, stronger than any single pairwise gap.

The two origin trailers enable the **self-preference cross-design**: with judges from
both the Claude and GPT families (§5), claimed-family × judge-family gives a 2×2 whose
interaction term is true self-preference, separated from a general "AI-disclosure"
or "family halo" effect. (An open-source judge as an additional neutral third
party is deferred to future work, §9.)

### 4.2 Per-axis invariance checks (run before freeze; any failure blocks it)

- **All variants:** `diff_patch` byte-identical to baseline — except `order_rev`,
  where the check is: the **multiset of per-file diff sections** is identical, only
  their order differs.
- **Non-description axes** (5–9): description byte-identical to baseline (for
  `repo_masked`, identical after the name substitution only).
- **Verbosity variants:** token count within ±20% of the target ratio; log all counts.
  Two pre-registered exemption classes make the check non-blocking (logged, not
  waived silently): (a) `short_desc` PRs (§3); (b) **terse waivers** (config
  `variants.terse_waivers`) — PRs whose descriptions are dominated by content the
  rewrite rules forbid compressing (fenced code, template headings, inline JSON
  examples, URLs), making the 0.5× band unreachable without dropping facts
  (`coreos-assembler__4359`, `espnet__6248`, `openbao__1906`, `zod__5672`; plus
  the v2-pool additions registered 2026-07-29 with the cc-v1 rewrites, before any
  v2 judging: `agents__4713`, `coreos-assembler__4386`, `effect__5952`,
  `espnet__6325`, `espnet__6356`, `node-postgres__3547`). The
  `verb_terse` cells of both classes are excluded from the terse arm of the
  dose–response analysis; their baseline/pad cells remain. For `openbao__1906`
  the terse text is byte-identical to baseline: no compressible prose exists
  under the cc-v1 rules.
- **LLM rewrites (2–4):** manual spot-check of ≥20% of outputs for **semantic
  leakage** (facts added or dropped). Failures are regenerated or hand-fixed; the
  check is re-run on fixes.

### 4.3 Known limitation, stated up front

`repo_masked` cannot scrub repo identity from file paths, imports, or code inside the
diff without violating the diff-frozen invariant. The axis therefore measures the
effect of **explicit repo labeling**, and any measured effect is a **lower bound** on
the true prestige/memorization effect. Report it as such.

### 4.4 Combos: deferred with a pre-committed rule

No combo variants in v1. **Pre-registered rule (committed now, before any results):**
after the main run, construct combo variants from the two axes with the largest
median |Δscore|, and test for super-/sub-additivity against the sum of the individual
effects. Combos ship as `variants_v2`, judged under the identical frozen prompt;
the append-only runner (§5) makes this a pure addition, no re-runs.

### 4.5 Rewrite construction: Claude Code skill (no API)

The three verbosity rewrites are authored by **Claude (Opus 4.8, high reasoning)
running in Claude Code**, following the frozen rule set `cc-v1` in
`.claude/skills/rewrite-variants/SKILL.md` — the same semantic-invariance rules
as the v1 API prompt, with tool-verified word counts. Interface: script 01
emits `rewrites_pending.json` (work queue with precomputed cache keys and
word-count bands) for any missing rewrite; the skill fills
`rewrites_cache.json`; script 01 re-runs to verify (§4.2 checks unchanged) and
freeze. Provenance (`model`, `prompt_version: cc-v1`, `method:
claude-code-skill`) is recorded per rewrite in the cache and in each variant's
construction metadata. The rewrites are regenerable through the same interface
by any other construction model (the cache is the drop-in boundary).

**Limitation (record in paper):** the construction model is Claude-family — the
same family as the Claude judge. Verbosity rewrites may therefore carry a
Claude stylistic fingerprint that interacts with self-preference for that judge.
Consequence for analysis (§6): the style-constant **dose–response among the
three rewrites** (terse → 2× → 4×, all same-styled) is the primary verbosity
contrast; variant-vs-baseline Δ additionally conflates length with
rewrite-style and is reported as secondary. The spot-check gate (§4.2) is
unchanged and remains human-performed.

**Frozen artifact:** `variants_v1/` — one JSON per (task_id, variant) containing the
fully assembled judge input fields + construction metadata (rewrite model, seeds,
check results).

## 5. Stage 2 — Judging runs

- **Judges (2), pinned 2026-07-25:** `claude-sonnet-5` (Claude family) and
  `gpt-5.6-terra` (GPT family). Exact model version strings logged per call.
  The Claude judge is deliberately a different model from the construction model
  (`claude-opus-4-8`) — same family (disclosed limitation, §4.5) but not the same
  model. An open-source judge is deferred to future work (§9).
- **Prompt:** one fixed template for all runs, modeled on config_A's layer order
  (task/rubric → title+description → diff → metadata), with the description and
  metadata as the perturbable slots.

### 5.1 System prompt principles

- Role: senior code reviewer assessing a pull request for merge-readiness.
- Contains the checklist items (§5.2) verbatim; fixed and versioned across
  all runs; identical for all judges.
- **No debiasing instructions** (no "ignore description style/authorship"): we
  measure default deployed behavior. The prompt never hints at the perturbation
  axes. (A debiasing-instruction arm is future work.)

### 5.2 Structured output: binary checklist (identical JSON schema for all
judges, enforced via each API's structured-output mode)

Scoring-interface rationale: direct numeric scoring exhibits documented
pathologies — central-tendency compression, score-ID and rubric-order bias,
number-token clustering (Evaluating Scoring Bias in LLM-as-a-Judge, 2506.22316;
Auditing Multimodal LLM Raters, 2605.16386). Binary decomposition is the
established fix: CheckEval (2403.18771) improved cross-evaluator agreement by
0.45 vs. Likert; HealthBench and PaperBench (2025) both use binary criteria
aggregated outside the model. We therefore use a **fixed 10-item binary
checklist** — identical for every PR and every variant — as the sole scoring
interface. **The judge never emits an aggregate number**; aggregation happens in
analysis (§6), which removes numeric-emission biases from the aggregate entirely.

Field order is deliberate — findings before judgments:

1. `issues`: up to 5 of `{file, approx_line, severity: critical|major|minor,
   description}`; empty list allowed.
2. `checklist`: 10 items, each `{answer: yes|no, evidence: "<one line, citing
   the diff or description>"}`. Items (final frozen wording in the prompt
   artifact):
   1. Introduces a plausible correctness bug or regression
   2. Adequately handles error/edge cases in the code it touches
   3. Changes are covered by new or updated tests
   4. Scoped to one coherent purpose
   5. Introduces a security or data-safety concern
   6. Introduces an obvious performance regression
   7. Consistent with the surrounding code's conventions
   8. Understandable without external context
   9. A competent reviewer would request changes before merging
   10. I would approve this PR as-is
3. `justification`: ≤ 40 words.

Item polarity is deliberately mixed (items 1, 5, 6, 9 are unfavorable-if-yes) to
counter acquiescence bias; polarity is normalized in analysis. The required
`evidence` line grounds each answer and feeds the mechanism analysis (§6).
Items serve **bias localization**: e.g., padding flipping item 8
(understandability) is semi-defensible; padding flipping item 1 or 3 —
assessments of code the padding never touched — is the damning finding.
Item 9 is the direct head-to-head with the human `has_requested_changes` signal;
item 10 is the decision metric (no post-hoc score threshold needed).

Known trade-off (limitations): binary items cannot register sub-threshold
shifts — a perturbation that nudges without flipping any item reads as zero.
The 10-item aggregate (an effective 0–10 ordinal) partially mitigates this.
A holistic-0–100 comparison arm ("is checklist scoring more perturbation-robust
than holistic scoring?") is deferred to future work (§9). Halo effects between
items answered in a single call (cf. Autorubric, 2603.00077, which isolates
criteria in separate calls at ~10× cost) are likewise acknowledged in
limitations.
- **Trials:** 3 per cell at provider-default temperature (the run-to-run consistency
  metric requires nonzero temperature to be meaningful).
- **Execution:** resumable runner over the full matrix, keyed by
  hash(task_id, variant, judge, trial); one JSONL row per call with raw response,
  token counts, model version, timestamp. Call order shuffled across conditions so
  provider drift cannot correlate with any axis. Crash/rate-limit safe by
  construction.
- **Scale/cost:** 40 PRs × 9 variants × 2 judges × 3 trials = **2,160 calls** at
  ~1–8k input tokens — roughly $10–30 total; runs overnight on a laptop.

**Artifact:** `results_v1.jsonl` (append-only, never edited).

### 5.3 Batch mode (cost — no effect on the instrument)

Anthropic's Message Batches API and OpenAI's Batch API each give a 50%
discount on input+output tokens, same models, <=24h completion window. The
final battery (2,160 calls) defaults to batch on cost grounds; the
synchronous runner stays available for pilots, prompt tuning, dry-runs, and
mop-up of cells that exhaust their batch resubmits. Both modes call the identical
request-construction code (`build_params` on each judge client) and write the
identical JSONL row schema, tagged with an `api_mode` (`sync`/`batch`)
provenance field — resume and Stage-3 analysis are mode-agnostic. `--batch`
on script 02 is a single idempotent "advance" step (collect finished
batches → submit what's missing → report), re-run until complete, mirroring
the sync resume philosophy rather than exposing separate submit/poll/collect
subcommands. No change to prompts, schema, trials, or temperature — cost
work never touches the instrument.

## 6. Stage 3 — Analysis (pure pandas; never calls an API)

Two orthogonal judge properties are measured; the study's primary claim is about
the first, the second anchors its interpretation:

- **Robustness (primary):** does the score move under meaning-preserving
  perturbation? (Δscore ≈ 0 is good.)
- **Validity (anchor):** does the *baseline* judgment track human reviewer
  signal? Head-to-head: checklist item 9 ("reviewer would request changes")
  vs. the actual `has_requested_changes` — direct binary agreement, plus
  Spearman of the aggregate 0–10 score with `requested_change_count`. A judge with
  near-zero perturbation sensitivity **and** near-zero validity is vacuously
  stable (the constant-75 judge), not a good judge — robustness is necessary,
  not sufficient. Each judge is placed on a 2D characterization
  (validity × worst-case bias magnitude); the quadrant it lands in is a result,
  not a complication. Note the sensitive+valid quadrant as the most dangerous
  deployment profile: right on average, swayed by surface features.

Caveat (limitations section): human comments were written during review, possibly
against pre-fix revisions, while `diff_patch` is the merged state — so validity
correlations are lower bounds. This does not affect the bias measurement, which
never uses human data.

- **Aggregate score:** computed in analysis, never by the model —
  polarity-normalize the 10 items, sum to a 0–10 score (unweighted in v1;
  any weighting must be pre-registered before results are seen).
- **Primary:** Δ(aggregate score) = variant − same-PR baseline, per (PR, judge,
  axis). Paired analysis: mixed-effects model with PR as random intercept
  (Wilcoxon as a robustness check). Rank axes by effect size per judge.
- **Per-item flip rates (bias localization):** for each axis × item, the rate at
  which the perturbation flips the item vs. baseline — which judgments absorb
  each perturbation (e.g., does padding flip `understandable` or
  `covered-by-tests`?). This is the most interpretable, quotable output of the
  study.
- **Issue matching (secondary):** match judge-reported `issues` to human-flagged
  locations (same file, line within the human comment's `diff_hunk` range).
  At baseline: detection overlap with human reviewers (validity evidence).
  Under perturbation: detection shift — does the judge stop seeing human-flagged
  issues (e.g., under 4× padding)? Score shift + detection shift = mechanism story.
- **Noise floor:** trial-to-trial item flip rate on identical input (3 trials
  per cell); every reported flip rate and Δ is compared against it. The
  `placebo` axis must show ≈ 0 effect — if it doesn't, the noise model is wrong
  and results are not reported until resolved.
- **Verbosity:** test monotonic trend in the aggregate score. Primary contrast:
  terse → 2× → 4× (style-constant, all construction-model-rewritten, §4.5);
  secondary: against the human-styled baseline (conflates length with
  rewrite-style).
- **Self-preference:** 2×2 claimed-family × judge-family; the interaction term is the
  self-preference estimate.
- **File order / tests position:** every selected PR mixes test and non-test
  files (§3 filter 3), so the tests-position contrast (did reversal move tests
  to the front?) is analyzable across the full pool, not a subgroup.
- **Covariates:** issue seriousness (`requested_change_count`,
  `has_requested_changes`), difficulty type, language.
- **Decision metric:** flip rate of item 10 ("approve as-is") under each
  perturbation — a real decision flip, no post-hoc score threshold required.
- **Mechanism evidence:** mine logged justifications — e.g., does `repo_masked`
  suppress project-name references; do verbosity variants elicit praise of
  "thorough documentation"? Reported as qualitative support per axis.

## 7. Consistency guarantees

Every stage reads only the frozen artifact of the previous stage. Prompts, seeds,
filters, and model versions are pinned and logged. All raw responses are retained.
Any number in the paper is regenerable from artifacts.

## 8. Decisions log

| Decision | Choice | Rationale |
|---|---|---|
| Buggy/clean binary | Dropped; severity covariate instead | SWE-PRBench has no defect-free PRs; primary within-PR metric doesn't need the binary |
| Description source | `prs.jsonl` `description` field | Present in data (README understates fields); no GitHub API needed |
| Reuse frozen contexts | No; own fixed template | Contexts lack a description slot; comparability to their leaderboard is irrelevant to a within-PR shift metric |
| Judges | Claude + GPT + open (3) | Two families required for self-preference cross; open judge gives frontier-vs-open comparison and neutral control |
| Tone/confidence axis | Dropped from v1 | Scope control (user selection) |
| Format/markdown axis | Dropped from v1 | Scope control (user selection); baseline keeps original formatting, so no canonicalization pass needed |
| Unverifiable claims axis | Dropped | CI verifies test claims mechanically in realistic pipelines; judge is not replacing CI. Future work: claims CI cannot check ("manually tested on device", local benchmarks) |
| Author persona / typos axes | Dropped from v1 | Scope control |
| Origin levels | Claude trailer + GPT trailer + none | Both trailers kept to preserve the identified self-preference 2×2; realistic `Co-Authored-By` format matches actual coding-agent output |
| File-order manipulation | Uniform seeded reversal; tests-position contrast pool-wide | Selection requires mixed test/non-test files, so the contrast is defined for every selected PR |
| Selection pool | eval_100, all 40 eligible PRs (no sampling) | Documented provenance from the paper's curated split; filters already consume the margin a random-sampling step would need; 142 additional eligible PRs exist in the full 350 as a pre-registered extension pool if more power is needed |
| AI-authored PRs | Screened out via description disclosure scan (e.g., "🤖 Generated with Claude Code") | Pre-existing authorship disclosures contaminate the origin axis baseline ("no claim"); recorded as a limitation — the origin axis measures the label effect on human-authored code |
| Short-description PRs (<150 chars) | Kept, flagged; sensitivity check in verbosity analysis | Legitimate real PRs; verbosity axis compressed for them but other axes unaffected |
| Combos | Deferred to v2 with pre-committed selection rule | Informative combos depend on main effects; pre-committed rule avoids forking-paths critique |
| Placebo axis | Kept | One cheap variant that validates the noise model for all other axes |
| Output schema | Issues list + fixed 10-item binary checklist + justification; no numeric score from the model | Direct scoring shows central-tendency/score-ID pathologies (2506.22316, 2605.16386); binary decomposition improves agreement by 0.45 (CheckEval); HealthBench/PaperBench precedent; aggregation in analysis removes numeric-emission bias; item 9 gives direct comparability to human `has_requested_changes` |
| Holistic 0–100 comparison arm | Deferred to future work | Checklist-only halves cost and keeps one clean protocol; the interface-comparison question remains open |
| Human comparison | Validity anchor + 2D judge characterization, not a target metric | Bias (robustness) and accuracy (validity) are orthogonal; consistent-but-invalid judges are vacuously stable, and the quadrant placement is itself a result |
| Issue matching | v1 secondary analysis | `file`/`line`/`diff_hunk` in annotations make location matching scriptable; adds detection-shift mechanism evidence |
| Debiasing instructions in prompt | Excluded | We measure default deployed behavior; a debiasing-instruction arm is future work |
| Rewrite construction | Claude Code skill (Opus 4.8, rule set cc-v1), no API | Zero marginal cost on subscription; validity is enforced by the unchanged §4.2 invariance checks + human spot-check, not by the generator; cache interface keeps rewrites regenerable by any model. Limitation: construction model shares the Claude judge's family (§4.5) — style-constant rewrite-only dose-response is the primary verbosity contrast |
| Batch judging for the final run | Adopted for Claude/GPT via each provider's Batch API; open judge stays sync (no batch API) | 50% off input+output tokens, quality-identical per provider docs (same models) — pure cost saving on a 3,240-call battery; `api_mode` provenance field on every row keeps sync and batch rows indistinguishable to Stage-3 analysis; idempotent single-command "advance" step avoids a submit/poll/collect subcommand surface |
| Terse-infeasible PRs (4 in v1, +6 in the v2 pool) | Waiver list (`terse_waivers`), not a relaxed counting rule; their `verb_terse` cells excluded from the terse analysis arm; decided 2026-07-25, extended 2026-07-29 with the v2 rewrites, both before any judging | Descriptions dominated by incompressible content (code blocks, template headings, JSON examples, URLs) cannot reach the 0.5× band without dropping facts — a counting trick (prose-only ratios) would not save the heading-dominated case and hides the issue; an explicit pre-registered list is deterministic and honest. Full matrix still runs (waived terse cells double as extra noise data). The v2 rate is higher (6 of 18 newly authored, floors 0.68–0.89) because the Type1_Direct pool is shorter and denser in fixed scaffolding — e.g. `espnet__6325`'s CER table alone is 108 words against a 181-word ceiling; the terse arm therefore runs at n=19 of 30 (6 new waivers + 3 v1 waivers still in pool + 2 `short_desc`) while the pad2x/pad4x arms keep n=30 |
| Typo preservation in rewrites | `openbao__1906` terse redone byte-identical to baseline after the original rewrite silently corrected the author's typos ("Is it save" → "is it safe") | Grammar/typo quality is an uncontrolled register perturbation the cc-v1 "keep the author's register" rule already forbids; compliance fix, no rule change, so no cc-v1 version bump or cache invalidation |
| Judge pin (2026-07-25) | `claude-sonnet-5` + `gpt-5.6-terra`, undated aliases (open-source judge dropped from v1, deferred to future work — supersedes the "Judges (3)" row above); both at `reasoning_effort: high`; context window left at each provider's live default (Claude 1M, GPT-5.6 Terra 1.05M), recorded not requested; no dated snapshot pinned | Two judges preserve the full self-preference 2×2 (claimed-family × judge-family); the open judge was a neutral-control nice-to-have, not required by any primary analysis. Pinning Sonnet 5 (not Opus 4.8) also ensures the Claude judge is not the same model as the rewrite construction model — same family remains a disclosed limitation (§4.5). Matrix shrinks 3,240 → 2,160 calls. `reasoning_effort: high` is pinned explicitly on both judges (Sonnet 5's own default; matched onto GPT-5.6 Terra too) so the effort level is comparable across providers rather than left to divergent per-provider defaults, and is logged verbatim per row. Snapshot check on 2026-07-25 (`models.retrieve`/`models.list`, both providers) found no dated snapshot id for either model — only the undated alias exists — so the alias is pinned as-is; the runner's per-row logged `model_version` (§7) is the reproducibility record if a provider later moves the alias. Context window is not an API request parameter (no beta header, e.g. Anthropic's legacy `context-1m` header, is ever sent); the values recorded are each model's live provider-default context length (Claude: `max_input_tokens` from `models.retrieve`; GPT-5.6 Terra: published model-card context, distinct from the unrelated 272k input-token higher-usage pricing threshold) — provenance metadata only, not a choice we can or do make |
| Reasoning effort → medium (2026-07-25) | Both judges repinned from `high` to `medium` (supersedes the effort part of the judge-pin row above); `max_output_tokens` raised 2,048 → 8,000 → 12,000 | Hidden reasoning tokens bill as output tokens and dominated dry-run spend (at `high`, ~4.2–4.8k output tokens on small PRs; at the original 2,048 cap, reasoning consumed the entire budget leaving zero visible JSON — billed but unparseable). Medium halves-plus the reasoning spend while keeping effort matched across providers. LIMITATION: all results characterize judges at medium effort; whether the measured biases grow or shrink at higher reasoning levels is future work (§9). 12k cap = ~2.5× observed usage headroom for pad4x variants, still under the sync no-streaming SDK guard |
| Judge prompt v2 (2026-07-25, pre-battery) | v1 + one unseen-diff-context guard sentence; user template, schema, and checklist unchanged; final battery frozen on v2 | Dry run caught the Claude judge reporting "missing import → NameError" issues for `itertools`/`contextlib` uses whose imports live in unchanged hunks the diff doesn't show — false positives that fed item 1. The guard ("never report an issue solely because something is not visible in the diff") is a factuality clarification, not debiasing: it names no perturbation axis and does not tell the judge to ignore surface properties, so §5.1's no-debiasing rule is intact. Dry-run health otherwise: no degenerate all-yes/all-no vectors, correct item-9/10 polarity, identical cross-judge answer vectors on one PR; watch-item for the pilot — all 4 dry-run responses answered item 9 "yes" (possible harsh-judge ceiling vs the 13/40 human `has_requested_changes` base rate) |
| Selection v2 + variants v2 (2026-07-29, pre-analysis) | Pool restricted to Type1_Direct (n=30 of the 40 Type1 in eval_100 pass the remaining filters); `order_rev` axis dropped (8-variant matrix); the test/non-test-mix filter dropped with it; versions bumped selection v1→v2, variants v1→v2, results v1→v2; the 360 already-collected claude cells of `results_v1` (trial 1 of 3) discarded **without being analyzed** | Validity: the judge's entire input is the diff, and only Type1_Direct PRs have their human-flagged issues directly visible in the changed hunks — Type2/Type3 ground truth is partly invisible to the instrument (concern first raised at dry-run review, 2026-07-25, before any battery results existed). `order_rev` was the weakest axis (single binary flip, no dose structure, no theoretical hook) and the sole reason for the test/non-test-mix filter; dropping both together grows the eligible Type1 pool 12→30, giving a homogeneous pool at nearly the original n. Matrix shrinks 2,160 → 1,440 cells, more than recouping the discarded rows. The 12 v1-selected Type1 PRs keep their cached verbosity rewrites (cache keys are task-scoped); 18 new PRs enter the cc-v1 rewrite queue. Pre-registered terse waivers carry over (espnet__6248 leaves the pool; any new-PR waivers must be registered before judging starts) |

## 9. Future work (out of scope for v1)

Unverifiable-claims axis (CI-uncheckable claims), tone/confidence, format/structure,
author persona, typo injection, comment-density in code (requires a separate variant
class that relaxes the diff-frozen invariant), combo variants per the §4.4 rule,
a debiasing-instruction arm (does adding "ignore surface properties" to the
system prompt reduce the measured bias?), a holistic-0–100 scoring arm (is
checklist scoring more perturbation-robust than holistic scoring? — connects
CheckEval to the bias literature), an open-source judge (e.g. a hosted
Llama-class model) as a neutral third family and frontier-vs-open comparison
(dropped from v1 at judge-pin time, §8), reasoning-level sensitivity (all v1
results are measured at `reasoning_effort: medium`, §8 — do the biases grow or
shrink at high/xhigh effort, and does higher effort buy robustness?), and
per-criterion isolated calls (Autorubric-style) to eliminate within-call halo
effects.

## 10. Key related work (for positioning)

- **Bias in the Loop: Auditing LLM-as-a-Judge for Software Engineering**
  (arXiv 2604.16790, 2026) — closest existing work: 12 prompt-injected biases in
  *pairwise A/B code evaluation*. We differ: real PRs (not snippets), absolute
  judgment (not pairwise), within-PR shift as the metric, trailer-based
  self-preference cross-design, and a human-reviewer validity anchor. Must be
  cited and positioned against explicitly.
- **CheckEval** (2403.18771), **HealthBench**, **PaperBench** (2025) — binary
  checklist/rubric scoring precedent (§5.2).
- **Evaluating Scoring Bias in LLM-as-a-Judge** (2506.22316), **Auditing
  Multimodal LLM Raters** (2605.16386), **Hidden Measurement Error in LLM
  Pipelines** (2604.11581) — numeric-scoring pathologies motivating the
  checklist interface.
- **Shi et al. 2026 ("Judging the Judges"), Zheng et al. 2023, Saito et al.
  2023, Wataoka et al. 2025** — controlled bias-pair paradigm on generic
  content (from the proposal).
