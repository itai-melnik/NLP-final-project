#!/usr/bin/env python3
"""Stage 0 — build the frozen PR selection manifest (spec §3).

Deterministic: re-running produces a byte-identical manifest. Verifies the
result against the spec's audited composition and fails loudly on mismatch.

    python scripts/00_build_selection.py [--config config/experiment.yaml]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prjudge.config import load_config
from prjudge.data import select_prs

# Spec §3 known-good composition — the manifest must reproduce these exactly.
# n=40 under strict (principled) test-file detection: spyder__24990 is excluded
# because its only "test-looking" file (kernelspec.py) is a false positive — it
# has no genuine test/non-test mix. See spec §3 selection note.
EXPECTED = {
    "n": 40,
    "difficulty": {"Type1_Direct": 12, "Type2_Contextual": 15, "Type3_Latent_Candidate": 13},
    "has_requested_changes": {"False": 27, "True": 13},
    "n_repos": 25,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=None, help="path to experiment.yaml")
    args = ap.parse_args()

    config = load_config(args.config)
    manifest = select_prs(config)
    comp = manifest["composition"]

    # -- audit against the spec's frozen numbers --------------------------
    problems: list[str] = []
    if comp["n"] != EXPECTED["n"]:
        problems.append(f"n={comp['n']} (expected {EXPECTED['n']})")
    if comp["difficulty"] != EXPECTED["difficulty"]:
        problems.append(f"difficulty={comp['difficulty']} (expected {EXPECTED['difficulty']})")
    if comp["has_requested_changes"] != EXPECTED["has_requested_changes"]:
        problems.append(
            f"has_requested_changes={comp['has_requested_changes']} "
            f"(expected {EXPECTED['has_requested_changes']})"
        )
    if comp["n_repos"] != EXPECTED["n_repos"]:
        problems.append(f"n_repos={comp['n_repos']} (expected {EXPECTED['n_repos']})")

    print(f"Selected {comp['n']} PRs from {manifest['pool_size']} pool")
    print(f"  difficulty:            {comp['difficulty']}")
    print(f"  language:              {comp['language']}")
    print(f"  has_requested_changes: {comp['has_requested_changes']}")
    print(f"  repos:                 {comp['n_repos']}")
    print(f"  short-desc PRs:        {comp['n_short_desc']}")
    print(f"  config_hash:           {manifest['config_hash'][:16]}...")

    if problems:
        print("\nAUDIT FAILED — composition does not match the spec:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    out_path = config.artifacts_dir / f"selection_manifest_{manifest['version']}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    print(f"\nAudit passed. Wrote {out_path.relative_to(config.artifacts_dir.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
