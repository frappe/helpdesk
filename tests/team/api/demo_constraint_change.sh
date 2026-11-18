#!/usr/bin/env bash
# Show the effect of changing two constraints in the spec.
#   1. NewTicket.subject / TicketUpdate.subject  maxLength 140 -> 100
#   2. TicketUpdate.priority                     enum gains "Critical"
# The generator is rerun on the changed spec, the two data sets are compared,
# and the generated tests are run against the new data. The system under test
# is unchanged, so exactly the cases that encode the new constraints must fail.
set -uo pipefail
APP_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
PY="${BENCH_PYTHON:-$APP_DIR/../../env/bin/python}"
API="$APP_DIR/tests/team/api"
OUT="$API/evidence"
mkdir -p "$OUT"
cd "$APP_DIR"

sed -e 's/maxLength: 140/maxLength: 100/' \
    -e 's/enum: \[Low, Medium, High, Urgent\]/enum: [Low, Medium, High, Urgent, Critical]/' \
    -e 's/^  version: 1.0.0/  version: 1.1.0/' \
    "$API/openapi.yaml" > "$OUT/openapi_changed.yaml"

{
  echo "== spec diff (original -> changed)"
  diff "$API/openapi.yaml" "$OUT/openapi_changed.yaml"
  echo
  echo "== generator on the original spec"
  "$PY" "$API/generate_testdata.py" --out "$API/generated/testdata.json"
  echo
  echo "== generator on the changed spec"
  "$PY" "$API/generate_testdata.py" --spec "$OUT/openapi_changed.yaml" --out "$OUT/testdata_changed.json"
  echo
  echo "== cases that differ"
  "$PY" - "$API/generated/testdata.json" "$OUT/testdata_changed.json" <<'EOF'
import json, sys
def load(path):
    return {(c["operationId"], c["input"], c["class"]): c for c in json.load(open(path))["cases"]}
old, new = load(sys.argv[1]), load(sys.argv[2])
for key in sorted(old.keys() - new.keys()):
    print("  removed:", " | ".join(key), "-> valid" if old[key]["valid"] else "-> invalid")
for key in sorted(new.keys() - old.keys()):
    print("  added:  ", " | ".join(key), "-> valid" if new[key]["valid"] else "-> invalid")
print(f"  total cases: {len(old)} -> {len(new)}")
EOF
  echo
  echo "== generated tests run with the changed data (system unchanged)"
  SQE_TESTDATA="$OUT/testdata_changed.json" "$PY" -m pytest "$API/test_generated_inputs.py" \
      -p no:cacheprovider -q 2>&1 | grep -E '^(FAILED|ERROR)|passed|failed'
} 2>&1 | grep -v RuntimeWarning | tee "$OUT/constraint_change.txt"
