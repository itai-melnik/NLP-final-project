#!/usr/bin/env python
"""Stage 3b — semantic issue matching (Tier B validity; spec 2026-07-30).

Prompt `matcher-v2` is pairwise: one API call per (judge issue, human comment)
pair, answered with {reasoning, match, confidence}. Pair answers are aggregated
back to one verdict per issue, so the artifact keeps the spec's `verdicts` shape.

Pilot mode (default until the spot-check is approved):
    python scripts/03_match_issues.py --pilot [--model claude-opus-5]
Runs a deterministic stratified sample of unique matcher requests through the
direct Messages API, writes artifacts/matching_pilot_<model>.jsonl and the
human-readable artifacts/spotcheck_matching_pilot_<model>.md for manual review.

Full mode (only after pilot approval):
    python scripts/03_match_issues.py --full [--model claude-haiku-4-5]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge import matching as M  # noqa: E402
from prjudge.config import load_config  # noqa: E402
from prjudge.data import load_annotation  # noqa: E402
from prjudge.judge import AnthropicJudge  # noqa: E402

RUN_NAME = "results_v2"
PILOT_SIZE = 16  # 2 judges x (4 single-issue + 4 multi-issue)
MAX_TOKENS = 2500  # reasoning strings run long; 1000 truncated ~1% of pairs
WORKERS = 8


def located_comments(config, task_id: str) -> list[dict]:
    """Human comments with a file location — the matcher's ground-truth side."""
    ann = load_annotation(config, task_id)
    return [
        {"comment_id": c["comment_id"], "file": c["file"], "line": c.get("line"),
         "body": c.get("body") or ""}
        for c in ann.get("comments", []) if c.get("file")
    ]


def load_rows(config) -> list[dict]:
    rows = []
    path = config.artifacts_dir / "runs" / f"{RUN_NAME}.jsonl"
    for line in path.open():
        r = json.loads(line)
        parsed = r.get("parsed") or {}
        rows.append({"task_id": r["task_id"], "judge": r["judge"],
                     "variant": r["variant"], "trial": r["trial"],
                     "issues": parsed.get("issues") or []})
    return rows


def pilot_sample(requests: list[dict], seed: int) -> list[dict]:
    """Deterministic stratified sample: per judge, mix of 1-issue and multi-issue."""
    rng = random.Random(seed)
    sample = []
    for judge in ("claude", "gpt"):
        for multi in (False, True):
            pool = sorted((r for r in requests
                           if r["judge"] == judge and (r["n_issues"] > 1) == multi),
                          key=lambda r: r["match_key"])
            rng.shuffle(pool)
            sample.extend(pool[:PILOT_SIZE // 4])
    return sample


def call_pair(client: AnthropicJudge, pair: dict) -> dict:
    """One pairwise matcher call; returns the pair enriched with its answer."""
    import anthropic

    resp, err = None, None
    for attempt in range(4):
        try:
            resp = client.judge(pair["system"], pair["user"], M.MATCHER_SCHEMA_V1,
                                max_tokens=MAX_TOKENS)
            err = resp.error
            break
        except (anthropic.RateLimitError, anthropic.InternalServerError) as e:
            err = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt * 5)
        except anthropic.BadRequestError as e:
            # "Grammar compilation timed out" is transient — retry; real 400s re-raise
            if "Grammar compilation" not in str(e) or attempt == 3:
                raise
            err = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt * 5)

    answer = M.sanitize_pair_answer(resp.parsed) if resp else None
    if answer is None and not err:
        # A returned-but-unusable answer (truncated / schema-violating JSON) must
        # not look like a clean "no match" downstream.
        err = "unparseable matcher answer"
    return {**{k: v for k, v in pair.items() if k not in ("system", "user")},
            "answer": answer,
            "model_version": resp.model_version if resp else None,
            "raw_text": resp.raw_text if resp else None,
            "error": err if answer is None else None,
            "input_tokens": resp.input_tokens if resp else None,
            "output_tokens": resp.output_tokens if resp else None}


def run_pairs(client: AnthropicJudge, pairs: list[dict]) -> list[dict]:
    """Fan the pairs out over a small thread pool, preserving input order."""
    done = [0]
    lock = threading.Lock()

    def work(pair):
        res = call_pair(client, pair)
        with lock:
            done[0] += 1
            if done[0] % 10 == 0 or done[0] == len(pairs):
                print(f"  ... {done[0]}/{len(pairs)} pairs", flush=True)
        return res

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(work, pairs))


def build_result_row(req: dict, pair_results: list[dict], *, model: str,
                     model_version: str | None) -> dict:
    """One artifact row per unique matcher request (spec §2)."""
    verdicts, dropped = M.verdicts_from_pairs(
        pair_results, n_issues=req["n_issues"], comment_ids=set(req["comment_ids"]))
    errors = [p["error"] for p in pair_results if p["error"]]
    return {
        "match_key": req["match_key"], "task_id": req["task_id"],
        "judge": req["judge"], "matcher_model": model,
        "matcher_model_version": model_version,
        "matcher_prompt_version": M.MATCHER_PROMPT_VERSION,
        "verdicts": verdicts, "n_dropped_verdicts": dropped,
        "n_pairs": len(pair_results),
        # raw_text is kept only for failures — otherwise it just duplicates answer.
        "pairs": [{"issue_idx": p["issue_idx"], "comment_id": p["comment_id"],
                   "answer": p["answer"], "error": p["error"],
                   **({} if p["answer"] else {"raw_text": p["raw_text"]})}
                  for p in pair_results],
        "error": errors[0] if errors else None,
        "input_tokens": sum(p["input_tokens"] or 0 for p in pair_results),
        "output_tokens": sum(p["output_tokens"] or 0 for p in pair_results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def write_spotcheck(path: Path, results: list[dict], reqs_by_key: dict) -> None:
    lines = ["# Matcher pilot spot-check — verify each verdict by hand",
             "",
             f"Matcher: `{results[0]['matcher_model_version']}` | prompt "
             f"`{M.MATCHER_PROMPT_VERSION}` (pairwise) | {len(results)} requests, "
             f"{sum(r['n_pairs'] for r in results)} pair calls",
             "",
             "Each judge issue was compared against every human comment separately.",
             "For each issue: ✅/❌ the matcher's verdict. A verdict is correct if the",
             "linked comment describes the SAME underlying problem (any phrasing/line),",
             "and `null` is correct when no comment does.", ""]
    for res in results:
        req = reqs_by_key[res["match_key"]]
        lines.append(f"---\n## {res['task_id']}  (judge: {res['judge']}, "
                     f"key `{res['match_key'][:8]}`)")
        comments = {c["comment_id"]: c for c in req["comments"]}
        lines.append("\n**Human comments:**")
        for cid, c in comments.items():
            body = " ".join(c["body"].split())
            lines.append(f"- `{cid}` {c['file']}:{c['line']} — {body[:300]}")
        lines.append("\n**Judge issues → matcher verdicts:**")
        verdict_by_idx = {v["issue_idx"]: v["comment_id"] for v in res["verdicts"]}
        pairs_by_idx: dict[int, list[dict]] = {}
        for p in res["pairs"]:
            pairs_by_idx.setdefault(p["issue_idx"], []).append(p)
        for idx, iss in enumerate(req["issues"]):
            v = verdict_by_idx.get(idx)
            tag = f"→ **matched `{v}`**" if v is not None else "→ **no match**"
            lines.append(f"- [{idx}] {iss.get('file')}:{iss.get('approx_line')} — "
                         f"{iss.get('description')}\n  {tag}")
            for p in pairs_by_idx.get(idx, []):
                a = p["answer"]
                if a is None:
                    lines.append(f"    - `{p['comment_id']}`: FAILED ({p['error']})")
                    continue
                mark = "match" if a["match"] else "no"
                lines.append(f"    - `{p['comment_id']}`: {mark} "
                             f"(conf {a['confidence']:.2f}) — {a['reasoning']}")
        if res["n_dropped_verdicts"]:
            lines.append(f"\n({res['n_dropped_verdicts']} pair answer(s) dropped)")
        lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--model", default="claude-opus-5")
    args = ap.parse_args()
    if not (args.pilot or args.full):
        ap.error("choose --pilot or --full")

    config = load_config()
    rows = load_rows(config)
    comments_by_task = {tid: located_comments(config, tid)
                        for tid in {r["task_id"] for r in rows}}
    requests = M.build_requests(rows, comments_by_task)
    print(f"rows: {len(rows)} | unique matcher requests: {len(requests)} | "
          f"pairs: {sum(r['n_issues'] * len(r['comment_ids']) for r in requests)}")

    # temperature is removed on Opus 5 / Sonnet 5-era models (400 if sent);
    # pin it to 0 only where still supported (Haiku 4.5).
    cfg = {"name": "matcher", "model": args.model}
    if "haiku" in args.model:
        cfg["temperature"] = 0
    client = AnthropicJudge(cfg)

    if args.pilot:
        sample = pilot_sample(requests, seed=int(config.get("seed", 0)))
        pairs = [p for req in sample for p in M.build_pairs(req)]
        print(f"pilot sample: {len(sample)} requests / {len(pairs)} pair calls "
              f"on {args.model}")

        pair_results = run_pairs(client, pairs)
        by_key: dict[str, list[dict]] = {}
        for p in pair_results:
            by_key.setdefault(p["match_key"], []).append(p)

        model_version = next((p.get("model_version") for p in pair_results
                              if p.get("model_version")), args.model)
        slug = args.model.replace(".", "-")
        out_path = config.artifacts_dir / f"matching_pilot_{slug}.jsonl"
        results = []
        with out_path.open("w") as f:
            for req in sample:
                res = build_result_row(req, by_key.get(req["match_key"], []),
                                       model=args.model, model_version=model_version)
                results.append(res)
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
                n_matched = sum(1 for v in res["verdicts"] if v["comment_id"])
                print(f"  {req['task_id']} ({req['judge']}) issues={req['n_issues']} "
                      f"pairs={res['n_pairs']} matched={n_matched}"
                      f"{' ERROR: ' + str(res['error']) if res['error'] else ''}")
        spot = config.artifacts_dir / f"spotcheck_matching_pilot_{slug}.md"
        write_spotcheck(spot, results, {r["match_key"]: r for r in sample})
        print(f"wrote {out_path} and {spot}")
        return

    raise SystemExit("--full is gated on pilot approval; not implemented yet")


if __name__ == "__main__":
    main()
