#!/usr/bin/env python3
"""Stage 1 — build the 9 variants per selected PR + invariance report (spec §4).

Reads the frozen selection manifest, assembles every (task_id, variant) judge
input, runs the per-axis invariance checks, and freezes the results. Refuses to
freeze (exit 1) if any blocking invariance check fails.

Deterministic variants are pure functions of the input. The three verbosity
variants call the construction model once and cache the result, so re-runs are
byte-identical unless --regenerate is passed.

    python scripts/01_build_variants.py                 # real construction model
    python scripts/01_build_variants.py --mock-construction   # offline, fake rewrites
    python scripts/01_build_variants.py --regenerate    # ignore the rewrite cache
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge.config import load_config
from prjudge.data import load_eval_pool
from prjudge.variants import (
    DETERMINISTIC_BUILDERS,
    VARIANT_IDS,
    VERBOSITY_VARIANTS,
    BuiltVariant,
    base_fields,
    build_verbosity,
    check_variant,
    generate_rewrite,
    rewrite_cache_key,
)


def _load_cache(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=None)
    ap.add_argument("--mock-construction", action="store_true",
                    help="fabricate verbosity rewrites offline (testing only; never for a real freeze)")
    ap.add_argument("--regenerate", action="store_true",
                    help="ignore the rewrite cache and regenerate all verbosity variants")
    ap.add_argument("--spotcheck-frac", type=float, default=0.20,
                    help="fraction of verbosity rewrites to emit for manual review (>=0.20)")
    args = ap.parse_args()

    config = load_config(args.config)
    version = config["versions"]["variants"]
    prompt_version = "v1"
    cm = config["variants"]["construction_model"]

    # -- inputs ------------------------------------------------------------
    manifest_path = config.artifacts_dir / f"selection_manifest_{config['versions']['selection']}.json"
    if not manifest_path.exists():
        print(f"missing {manifest_path}; run scripts/00_build_selection.py first", file=sys.stderr)
        return 1
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    task_ids = set(manifest["task_ids"])
    short_desc = {m["task_id"]: m["short_desc"] for m in manifest["prs"]}

    records = {r["task_id"]: r for r in load_eval_pool(config) if r["task_id"] in task_ids}
    missing = task_ids - set(records)
    if missing:
        print(f"selected task_ids missing from eval pool: {sorted(missing)}", file=sys.stderr)
        return 1

    out_dir = config.artifacts_dir / f"variants_{version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_path = out_dir / ("rewrites_cache.mock.json" if args.mock_construction else "rewrites_cache.json")
    cache = {} if args.regenerate else _load_cache(cache_path)

    # -- build -------------------------------------------------------------
    all_checks: list[dict] = []
    blocking_failures: list[dict] = []
    spotcheck_pool: list[dict] = []
    n_written = 0
    n_generated = 0

    for task_id in sorted(task_ids):
        rec = records[task_id]
        base = base_fields(rec)
        meta_short = {"short_desc": short_desc.get(task_id, False)}

        built: dict[str, BuiltVariant] = {}

        # deterministic variants
        for vid, builder in DETERMINISTIC_BUILDERS.items():
            ji, cons = builder(base, config)
            built[vid] = BuiltVariant(judge_input=ji, construction=cons)

        # verbosity variants (cached)
        for vid in VERBOSITY_VARIANTS:
            ck = rewrite_cache_key(task_id, vid, prompt_version, cm["model"])
            if ck in cache:
                rewrite_text = cache[ck]["text"]
            else:
                rewrite_text = generate_rewrite(base.description, vid, config, mock=args.mock_construction)
                cache[ck] = {
                    "text": rewrite_text,
                    "model": cm["model"],
                    "prompt_version": prompt_version,
                    "mock": args.mock_construction,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
                n_generated += 1
            ji, cons = build_verbosity(base, vid, rewrite_text)
            cons.update({"model": cm["model"], "prompt_version": prompt_version,
                         "mock": args.mock_construction})
            built[vid] = BuiltVariant(judge_input=ji, construction=cons)
            spotcheck_pool.append({"task_id": task_id, "variant": vid})

        # checks + write
        for vid in VARIANT_IDS:
            bv = built[vid]
            meta = {**bv.construction, **meta_short}
            bv.checks = check_variant(bv.judge_input, built["baseline"].judge_input, config, meta=meta)
            for c in bv.checks:
                row = {"task_id": task_id, "variant": vid, "check": c.name,
                       "passed": c.passed, "blocking": c.blocking, "detail": c.detail}
                all_checks.append(row)
                if c.blocking and not c.passed:
                    blocking_failures.append(row)

            payload = {
                "task_id": task_id,
                "variant": vid,
                "axis": _axis(vid),
                "judge_input": bv.judge_input.to_dict(),
                "construction": bv.construction,
                "checks": [{"check": c.name, "passed": c.passed, "blocking": c.blocking,
                            "detail": c.detail} for c in bv.checks],
                "prompt_version": prompt_version,
            }
            with open(out_dir / f"{task_id}__{vid}.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
                f.write("\n")
            n_written += 1

    if n_generated:
        _save_cache(cache_path, cache)

    # -- invariance report -------------------------------------------------
    report = {
        "version": version,
        "config_hash": config.hash(),
        "prompt_version": prompt_version,
        "construction_model": cm["model"],
        "mock_construction": args.mock_construction,
        "n_prs": len(task_ids),
        "n_variants_written": n_written,
        "n_checks": len(all_checks),
        "n_blocking_failures": len(blocking_failures),
        "blocking_failures": blocking_failures,
        "checks": all_checks,
    }
    report_path = config.artifacts_dir / f"invariance_report_{version}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    # -- spotcheck sample --------------------------------------------------
    _write_spotcheck(config, out_dir, records, spotcheck_pool, args.spotcheck_frac, version)

    # -- summary + gate ----------------------------------------------------
    n_warn = sum(1 for c in all_checks if not c["passed"] and not c["blocking"])
    print(f"Built {n_written} variant files for {len(task_ids)} PRs "
          f"({n_generated} rewrites generated{' [MOCK]' if args.mock_construction else ''}).")
    print(f"Invariance: {len(all_checks)} checks, {len(blocking_failures)} blocking failures, "
          f"{n_warn} non-blocking warnings.")
    print(f"Report: {report_path.relative_to(config.artifacts_dir.parent)}")

    if blocking_failures:
        print("\nFREEZE BLOCKED — blocking invariance failures:", file=sys.stderr)
        for r in blocking_failures[:20]:
            print(f"  - {r['task_id']}/{r['variant']}/{r['check']}: {r['detail']}", file=sys.stderr)
        return 1
    if args.mock_construction:
        print("\nNOTE: --mock-construction used; rewrites are NOT semantically faithful. "
              "Re-run without it (real API) before a real freeze.")
    return 0


def _axis(vid: str) -> str:
    from prjudge.variants import VARIANT_AXIS
    return VARIANT_AXIS[vid]


def _write_spotcheck(config, out_dir, records, pool, frac, version):
    frac = max(0.20, frac)
    rng = random.Random(config["seed"])
    k = max(1, round(len(pool) * frac))
    sample = rng.sample(pool, min(k, len(pool)))
    sample.sort(key=lambda d: (d["task_id"], d["variant"]))

    lines = [f"# Verbosity rewrite spot-check (v{version[-1] if version.startswith('v') else version})",
             "",
             f"Random {frac:.0%} sample ({len(sample)} of {len(pool)} rewrites) for manual",
             "semantic-leakage review (spec §4.2). Check: no fact added or dropped vs baseline.",
             ""]
    for item in sample:
        tid, vid = item["task_id"], item["variant"]
        with open(out_dir / f"{tid}__{vid}.json", "r", encoding="utf-8") as f:
            var = json.load(f)
        baseline_desc = (records[tid].get("description") or "").strip()
        lines += [f"## {tid} — {vid}", "",
                  "**Baseline description:**", "", "```", baseline_desc, "```", "",
                  "**Rewritten description:**", "", "```", var["judge_input"]["description"], "```",
                  "", "- [ ] No facts added  - [ ] No facts dropped  - [ ] Markdown preserved", "",
                  "---", ""]
    path = config.artifacts_dir / f"spotcheck_{version}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Spot-check sample: {path.relative_to(config.artifacts_dir.parent)} "
          f"({len(sample)} rewrites)")


if __name__ == "__main__":
    raise SystemExit(main())
