#!/usr/bin/env python3
"""Stage 2 — run judges over a run spec (spec §5). Same entry the notebook uses.

Resumable and crash-safe: rerun the same --run-name to continue. Pilot runs use
their own --run-name and are never mixed with the final results_v1.jsonl.

    # no-spend plumbing test (keying/resume) over the full matrix
    python scripts/02_run_judges.py --mock --run-name smoke

    # pilot: baseline only, one judge, 5 PRs, while tuning the prompt
    python scripts/02_run_judges.py --run-name pilot_p1 \\
        --variants baseline --judges claude --limit 5 --prompt-version v1

    # dry-run: 2 PRs x 1 variant x 1 judge x 1 trial against real APIs (~$0.10)
    python scripts/02_run_judges.py --dry-run

    # final full battery
    python scripts/02_run_judges.py --run-name results_v1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge.config import load_config
from prjudge.judge import resolve_run_spec, run_judges


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None)
    ap.add_argument("--run-name", default=None,
                    help="output file artifacts/runs/{run_name}.jsonl (default: config final_run_name)")
    ap.add_argument("--variants", nargs="+", default=None, help="subset of variant ids")
    ap.add_argument("--judges", nargs="+", default=None, help="subset of judge names")
    ap.add_argument("--prs", nargs="+", default=None, help="explicit task_ids")
    ap.add_argument("--limit", type=int, default=None, help="use only the first N selected PRs")
    ap.add_argument("--trials", type=int, default=None, help="trials per cell (default: config)")
    ap.add_argument("--prompt-version", default=None, help="frozen prompt version (default: config)")
    ap.add_argument("--mock", action="store_true",
                    help="use canned responses (no API, no key) to test keying/resume")
    ap.add_argument("--dry-run", action="store_true",
                    help="2 PRs x 1 variant x 1 judge x 1 trial against real APIs (schema check)")
    args = ap.parse_args()

    config = load_config(args.config)

    # --dry-run is a fixed tiny real-API spec (overrides subset flags).
    if args.dry_run:
        run_name = args.run_name or "dry_run"
        first_judge = config["judging"]["judges"][0]["name"]
        spec = resolve_run_spec(
            config, run_name=run_name, variants=["baseline"],
            judges=[first_judge], limit=2, trials=1,
            prompt_version=args.prompt_version,
        )
        mock = False
    else:
        run_name = args.run_name or config["judging"]["final_run_name"]
        if args.mock and run_name == config["judging"]["final_run_name"]:
            run_name = f"{run_name}_mock"   # never let mock rows land in the final file
        spec = resolve_run_spec(
            config, run_name=run_name, variants=args.variants, judges=args.judges,
            prs=args.prs, limit=args.limit, trials=args.trials,
            prompt_version=args.prompt_version,
        )
        mock = args.mock

    n = len(spec.cells())
    print(f"Run '{spec.run_name}': {len(spec.task_ids)} PRs x {len(spec.variants)} variants "
          f"x {len(spec.judges)} judges x {spec.trials} trials = {n} cells "
          f"(prompt {spec.prompt_version}){' [MOCK]' if mock else ''}")

    summary = run_judges(config, spec, mock=mock)

    print(f"\nDone. already={summary.already_done} attempted={summary.attempted} "
          f"ok={summary.succeeded} failed={summary.failed}")
    print(f"tokens: in={summary.input_tokens} out={summary.output_tokens}")
    print(f"output: artifacts/runs/{spec.run_name}.jsonl")
    if summary.errors:
        print(f"\n{len(summary.errors)} failures (first 10):", file=sys.stderr)
        for e in summary.errors[:10]:
            print(f"  - {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
