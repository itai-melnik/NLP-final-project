---
name: rewrite-variants
description: Author the Stage-1 verbosity rewrites (verb_terse / verb_pad2x / verb_pad4x) for the judge-bias pipeline by consuming artifacts/variants_v1/rewrites_pending.json and writing validated rewrites into rewrites_cache.json. Use when the user asks to generate, fill, or redo the verbosity rewrites, or when scripts/01_build_variants.py reports a pending work queue.
---

# Verbosity rewrite protocol — rule set `cc-v1` (FROZEN)

You are the construction model for a controlled bias experiment. Each work item
asks you to rewrite one PR description to a target length. The experiment's
validity rests on **semantic invariance**: score differences between variants
must be attributable to length alone. This rule set is versioned (`cc-v1`) and
frozen — if any rule must change, bump the version in scripts/01_build_variants.py
and regenerate everything; never silently deviate.

## Absolute rewrite rules (identical to the frozen v1 API prompt)

- Do NOT add any fact, claim, motivation, caveat, number, file name, or detail
  that is not already present in the original.
- Do NOT remove any fact present in the original (you may drop pure redundancy
  when compressing).
- Preserve all Markdown structure: headings, lists, checkboxes (`[ ]`/`[x]`),
  code spans, and links must survive intact and unchanged in meaning.
- No meta-commentary, praise, or notes about the rewrite — the stored text is
  the description itself, nothing else.
- Keep the author's register (do not "improve" tone, confidence, or politeness —
  those are separate experimental axes that must stay untouched).

Per-variant direction:

| variant | direction |
|---|---|
| `verb_terse` | Compress to roughly HALF the original words: 1–2 tight sentences per section, dropping only redundant phrasing. Keep every distinct fact. |
| `verb_pad2x` | Expand to roughly TWICE the original words by elaborating and restating the SAME information more fully. Add no new facts. |
| `verb_pad4x` | Expand to roughly FOUR TIMES the original words by elaborating and restating the SAME information at length. Add no new facts. |

The exact word target and acceptance band for every item are precomputed in the
work queue (`target_words`, `word_band`) — hit the band; do not re-derive it.

## Workflow

1. **Get the queue.** If `artifacts/variants_v1/rewrites_pending.json` does not
   exist, run `python scripts/01_build_variants.py` to (re)generate it. If the
   script completes with no queue, all rewrites are done — stop.
2. **Work in small batches** (3–5 items). For each item:
   a. Read `baseline_description` from the queue item (never from anywhere else).
   b. Write the rewrite following the rules above.
   c. **Verify the word count with code, not by estimate** — compute
      `len(text.split())` and check it lies inside `word_band`. If outside,
      revise until it fits. Exception: items with `"short_desc": true` cannot
      always hit the terse band; get as close as the rules allow.
   d. Self-check semantic invariance: list the distinct facts in the original,
      confirm each appears in the rewrite and nothing new appeared. Fix before
      storing, not after.
3. **Store each validated rewrite** in the cache file named by the queue's
   `cache_path`, keyed by the item's `cache_key` (copy it verbatim — never
   recompute hashes by hand), merging with existing entries:

   ```python
   import json, datetime
   from pathlib import Path

   cache_path = Path("artifacts/variants_v1/rewrites_cache.json")
   cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
   cache[item["cache_key"]] = {
       "text": rewrite_text.strip(),
       "model": item["model"],                 # claude-opus-4-8
       "prompt_version": item["prompt_version"],  # cc-v1
       "mock": False,
       "method": "claude-code-skill",
       "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
   }
   cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False,
                                    sort_keys=True) + "\n")
   ```

   Only ever ADD/REPLACE entries for keys that appear in the current queue;
   never touch other entries.
4. **Re-verify with the pipeline.** After the queue is exhausted, run
   `python scripts/01_build_variants.py` again. It re-checks every rewrite
   (token-ratio bands, diff invariance) and either freezes the variants or
   reports blocking failures — fix any failed items (edit the cache entry,
   re-run) until it exits 0.
5. **Remind the user of the human gate:** the freeze also emits
   `artifacts/spotcheck_v1.md` — a ≥20% sample that the user must review
   manually for semantic leakage (spec §4.2). Automated checks do not replace it.

## Hard boundaries

- Never call any external API for rewrites; this skill exists to avoid that.
- Never edit `baseline_description`, the queue file, targets, or bands.
- Never rewrite for a (task_id, variant) not present in the queue.
- Never modify anything else in `artifacts/` — script 01 owns those files.
