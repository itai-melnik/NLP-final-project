#!/usr/bin/env bash
# Poll `02_run_judges.py --batch` every 10 minutes until the run is complete.
#
# Usage:
#   scripts/poll_batch.sh [run-name] [extra args...]
#
#   scripts/poll_batch.sh                        # run-name = results_v1, --trials 1
#   scripts/poll_batch.sh results_v1 --trials 1  # explicit
#   scripts/poll_batch.sh results_v1             # full 3-trial battery (config default)
#
# Exit codes from 02_run_judges.py --batch (see its docstring):
#   0 = every cell in the spec is in the JSONL -> done, stop polling
#   2 = batches still in-flight              -> keep polling
#   1 = a cell needs a sync mop-up, or a hard error occurred -> stop, needs a human
#
# Ctrl-C to stop early; safe to re-run this script at any time (the underlying
# --batch step is idempotent).

set -euo pipefail

RUN_NAME="${1:-results_v1}"
shift || true
EXTRA_ARGS=("$@")
if [ "${#EXTRA_ARGS[@]}" -eq 0 ]; then
    EXTRA_ARGS=(--trials 2)
fi

INTERVAL_SECS=$((10 * 60))
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$REPO_ROOT/artifacts/runs/${RUN_NAME}.poll.log"

cd "$REPO_ROOT"

echo "Polling --batch for run '$RUN_NAME' every $((INTERVAL_SECS / 60)) min. Logging to $LOG_FILE"
echo "(Ctrl-C to stop; re-running this script later resumes safely.)"

while true; do
    TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    {
        echo "=== $TS ==="
        python scripts/02_run_judges.py --run-name "$RUN_NAME" --batch "${EXTRA_ARGS[@]}"
    } | tee -a "$LOG_FILE"
    STATUS="${PIPESTATUS[0]}"

    case "$STATUS" in
        0)
            echo "[$TS] All cells complete (exit 0). Stopping." | tee -a "$LOG_FILE"
            exit 0
            ;;
        2)
            echo "[$TS] Still in-flight (exit 2). Sleeping ${INTERVAL_SECS}s..." | tee -a "$LOG_FILE"
            sleep "$INTERVAL_SECS"
            ;;
        *)
            echo "[$TS] Needs attention (exit $STATUS) — sync mop-up or hard error. Stopping." | tee -a "$LOG_FILE"
            exit "$STATUS"
            ;;
    esac
done
