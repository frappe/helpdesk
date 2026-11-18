#!/usr/bin/env bash
# Seed or reset the synthetic test data.   Usage: bash tests/team/seed.sh seed|reset [site]
#          bash tests/team/seed.sh agent-reply --ticket <name>
#          bash tests/team/seed.sh setting --key <field> --value <value>
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BENCH_DIR="$(cd "$APP_DIR/../.." && pwd)"
cd "$BENCH_DIR/sites"
COMMAND="$1"; shift
case "$COMMAND" in
  seed|reset) "$BENCH_DIR/env/bin/python" "$APP_DIR/tests/team/seed/seed.py" "$COMMAND" --site "${1:-helpdesk.localhost}" ;;
  *)          "$BENCH_DIR/env/bin/python" "$APP_DIR/tests/team/seed/seed.py" "$COMMAND" "$@" ;;
esac
