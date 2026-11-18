#!/usr/bin/env bash
# OWASP ZAP in passive mode while the Playwright tests run both workflows.
# ZAP only observes the traffic that passes through it; no active scan or
# spider is started. Results go to tests/team/security/evidence/zap/.
#
# Usage (bench running):  bash tests/team/security/zap_passive.sh
set -euo pipefail
TEAM="$(cd "$(dirname "$0")/.." && pwd)"
ZAP_HOME="${ZAP_HOME:-$HOME/zap/ZAP_2.17.0}"
ZAP="http://127.0.0.1:8090"
TARGET="${SQE_BASE_URL:-http://127.0.0.1:8000}"
OUT="$TEAM/security/evidence/zap"
SESSION_DIR="$(mktemp -d)"
mkdir -p "$OUT"

zap_api() { curl -fsS "$ZAP/$1"; }

echo "== starting ZAP $(basename "$ZAP_HOME") in daemon mode (passive only)"
"$ZAP_HOME/zap.sh" -daemon -host 127.0.0.1 -port 8090 \
  -config api.disablekey=true \
  -config database.recoverylog=false \
  -config autoupdate.checkOnStart=false \
  -config autoupdate.installAddonUpdates=false \
  -config autoupdate.installScannerRules=false \
  -newsession "$SESSION_DIR/session" > "$OUT/zap_daemon.log" 2>&1 &
ZAP_PID=$!
trap 'curl -fsS "$ZAP/JSON/core/action/shutdown/" >/dev/null 2>&1 || kill $ZAP_PID 2>/dev/null; rm -rf "$SESSION_DIR"' EXIT
for i in $(seq 1 120); do
  zap_api "JSON/core/view/version/" >/dev/null 2>&1 && break
  sleep 2
done
echo "ZAP version: $(zap_api JSON/core/view/version/)"
echo "passive scanners enabled: $(zap_api JSON/pscan/view/scanners/ | python3 -c 'import json,sys; d=json.load(sys.stdin)["scanners"]; print(sum(s["enabled"]=="true" for s in d), "of", len(d))')"

echo "== running both workflows and the security checks through ZAP"
cd "$TEAM/e2e"
set +e
SQE_PROXY="$ZAP" npx playwright test usecases usability security --reporter=list > "$OUT/playwright_through_zap.log" 2>&1
PW_EXIT=$?
set -e
grep -E 'passed|failed' "$OUT/playwright_through_zap.log" | tail -3

echo "== waiting for the passive scanner to finish"
for i in $(seq 1 300); do
  left=$(zap_api JSON/pscan/view/recordsToScan/ | python3 -c 'import json,sys; print(json.load(sys.stdin)["recordsToScan"])')
  [ "$left" = "0" ] && break
  sleep 2
done

echo "== exporting"
zap_api "JSON/core/view/urls/?baseurl=$TARGET" > "$OUT/urls.json"
zap_api "JSON/core/view/alerts/?baseurl=$TARGET&start=0&count=100000" > "$OUT/alerts.json"
zap_api "JSON/core/view/numberOfMessages/?baseurl=$TARGET" > "$OUT/message_count.json"
zap_api "OTHER/core/other/htmlreport/" > "$OUT/zap_report.html"
python3 "$TEAM/security/zap_summary.py" "$OUT"
exit $PW_EXIT
