#!/usr/bin/env bash
# Run a Locust bench against the configured target host and tag the run.
#
# Usage:  ./run_bench.sh <tag> [host]
#   tag  = "baseline" or "after" (used in output filenames)
#   host = base URL of the server (default http://127.0.0.1:18080)

set -euo pipefail

TAG="${1:-after}"
HOST="${2:-http://127.0.0.1:18080}"
HERE="$(cd "$(dirname "$0")" && pwd)"
USERS=50
SPAWN=10
DURATION=60s

cd "$HERE"

uv run locust -f locustfile.py \
  --headless \
  --host "$HOST" \
  -u "$USERS" \
  -r "$SPAWN" \
  -t "$DURATION" \
  --csv="results_${TAG}" \
  --html="report_${TAG}.html" \
  --only-summary
