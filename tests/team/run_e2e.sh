#!/usr/bin/env bash
# Run the team's browser tests against the running bench.
# Usage: bash tests/team/run_e2e.sh [playwright args, e.g. usecases]
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP_DIR/tests/team/e2e"
[ -f ../.env ] || bash ../seed.sh seed
[ -d node_modules ] || npm ci
npx playwright test "$@"
