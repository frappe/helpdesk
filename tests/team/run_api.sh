#!/usr/bin/env bash
# Regenerate the API test data from the spec, then run the API and integration
# tests against the running bench.   Usage: bash tests/team/run_api.sh [pytest args]
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PY="${BENCH_PYTHON:-$APP_DIR/../../env/bin/python}"
OUT="$APP_DIR/tests/team/reports/api"
mkdir -p "$OUT"
cd "$APP_DIR"
[ -f tests/team/.env ] || bash tests/team/seed.sh seed
"$PY" tests/team/api/generate_testdata.py | tee "$OUT/generator_summary.txt"
"$PY" -m pytest tests/team/api -p no:cacheprovider --junitxml="$OUT/junit.xml" -q -rxX "$@"
