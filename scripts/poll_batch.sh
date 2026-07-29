#!/usr/bin/env bash
# Poll `02_run_judges.py --batch` every 10 minutes until the run is complete.
#
# Usage:
#   scripts/poll_batch.sh [run-name] [extra args...]
#
#   scripts/poll_batch.sh                        # run-name = results_v1, --trials 1 (quick check)
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
#
# This loop typically needs to survive many hours (each org-level
# enqueued-token-capped provider, e.g. OpenAI, only has one chunk in flight
# at a time — see prjudge.batch — so a ~2k-cell run walks through several
# sequential chunks). A `sleep`-based foreground loop dies with the terminal
# it's attached to, or when the machine sleeps. Run it so it survives both:
#
#   caffeinate -i nohup scripts/poll_batch.sh results_v1 \
#       > artifacts/runs/results_v1.poll.out 2>&1 &
#   disown
#
# (`caffeinate -i` blocks idle sleep only while this process runs; it does
# not stop explicit lid-close sleep. `nohup` + `disown` detach it from this
# terminal so closing the terminal/tab doesn't send it SIGHUP.)

set -euo pipefail

if [ "$#" -eq 0 ]; then
    RUN_NAME="results_v1"
    EXTRA_ARGS=(--trials 1)
else
    RUN_NAME="$1"
    shift
    EXTRA_ARGS=("$@")
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
        python scripts/02_run_judges.py --run-name "$RUN_NAME" --batch \
            ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
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
