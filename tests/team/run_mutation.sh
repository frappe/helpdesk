#!/usr/bin/env bash
# Mutation-test the business-rule scope with Cosmic Ray (core + custom operators).
# Runs in a sandbox copy of the source, so the working tree and a running bench
# are never mutated.   Usage:  bash tests/team/run_mutation.sh [threshold-percent]
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$(cd "$(dirname "${BENCH_PYTHON:-$APP_DIR/../../env/bin/python}")" && pwd)"
OUT="$APP_DIR/tests/team/reports/mutation"
SANDBOX="${MUTATION_SANDBOX:-$OUT/sandbox}"
THRESHOLD="${1:-}"

rm -rf "$SANDBOX"
mkdir -p "$SANDBOX"
cd "$APP_DIR"
tar -cf - --exclude='helpdesk/public' --exclude='helpdesk/locale' --exclude='__pycache__' \
    --exclude='tests/team/reports' helpdesk tests/team | tar -xf - -C "$SANDBOX"

export PATH="$BIN:$PATH"
export PYTHONPATH="$SANDBOX"
cd "$SANDBOX"
python - <<EOF
import helpdesk, sys
assert helpdesk.__file__.startswith("$SANDBOX"), f"not testing the sandbox copy: {helpdesk.__file__}"
EOF

# make the custom operators visible to Cosmic Ray's plugin loader
if command -v uv >/dev/null 2>&1; then
  uv pip install --python "$BIN/python" -q -e "$APP_DIR/tests/team/mutation/operators"
else
  python -m pip install -q -e "$APP_DIR/tests/team/mutation/operators"
fi
cosmic-ray operators | grep '^sqe/'

CONFIG=tests/team/mutation/cosmic-ray.toml
SESSION="$OUT/session.sqlite"
rm -f "$SESSION"
cosmic-ray init "$CONFIG" "$SESSION"
python tests/team/tools/mutation_scope_filter.py "$SESSION" --root "$SANDBOX"
cosmic-ray baseline "$CONFIG"
cosmic-ray exec "$CONFIG" "$SESSION"
if [ -n "$THRESHOLD" ]; then
  python tests/team/tools/mutation_report.py "$SESSION" --out "$OUT" --threshold "$THRESHOLD"
else
  python tests/team/tools/mutation_report.py "$SESSION" --out "$OUT"
fi
