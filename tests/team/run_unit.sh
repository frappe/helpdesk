#!/usr/bin/env bash
# Run the team's unit tests with statement + branch coverage of the rule scope.
# Usage (from anywhere):  bash tests/team/run_unit.sh
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${BENCH_PYTHON:-$APP_DIR/../../env/bin/python}"
OUT="$APP_DIR/tests/team/reports/unit"
mkdir -p "$OUT"
cd "$APP_DIR"
"$PY" -m pytest tests/team/unit \
  -p no:cacheprovider \
  --cov=helpdesk.helpdesk.doctype.hd_ticket \
  --cov=helpdesk.helpdesk.doctype.hd_ticket_status \
  --cov-branch \
  --cov-report=json:"$OUT/coverage.json" \
  --cov-report=xml:"$OUT/coverage.xml" \
  --cov-report=html:"$OUT/html" \
  --junitxml="$OUT/junit.xml" \
  -q "$@"
"$PY" tests/team/tools/scoped_coverage.py "$OUT/coverage.json" --threshold 100
