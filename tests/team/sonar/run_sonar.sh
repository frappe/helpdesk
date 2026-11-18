#!/usr/bin/env bash
# SonarQube analysis of Helpdesk, with the team's unit-test coverage imported.
#   1. refresh coverage.xml / junit.xml (run_unit.sh)
#   2. analyse the whole app (project "helpdesk", default "Sonar way" profiles)
#   3. analyse the business-rule files again with the "SQE complexity probe"
#      profile (project "helpdesk-complexity"), which reports every function's
#      cyclomatic and cognitive complexity
#   4. export measures, issues, hotspots and gate status to sonar/evidence/
# Needs the local server (bash tests/team/sonar/server.sh start) and
# SONAR_TOKEN in ~/.sqe-env (python sonar_admin.py init).
set -euo pipefail
TEAM="$(cd "$(dirname "$0")/.." && pwd)"
APP="$(cd "$TEAM/../.." && pwd)"
PY="$APP/../../env/bin/python"
SCANNER="${SCANNER:-$HOME/sonar/sonar-scanner/bin/sonar-scanner}"
export SONAR_URL="${SONAR_URL:-http://127.0.0.1:9100}"
OUT="$TEAM/sonar/evidence"
set -a; . "$HOME/.sqe-env"; set +a
mkdir -p "$OUT"
cd "$APP"

echo "== unit tests with coverage"
bash "$TEAM/run_unit.sh" > "$OUT/unit_run.txt" 2>&1 || { tail -20 "$OUT/unit_run.txt"; exit 1; }
tail -8 "$OUT/unit_run.txt"

scan() {  # scan NAME extra-args...
  local name="$1"; shift
  echo "== sonar-scanner: $name"
  rm -rf .scannerwork
  SONAR_TOKEN="$SONAR_TOKEN" "$SCANNER" \
    -Dproject.settings="$TEAM/sonar/sonar-project.properties" \
    -Dsonar.projectBaseDir="$APP" \
    -Dsonar.host.url="$SONAR_URL" \
    -Dsonar.scm.disabled=false \
    "$@" > "$OUT/scanner_$name.log" 2>&1 || { tail -40 "$OUT/scanner_$name.log"; exit 1; }
  grep -E "ANALYSIS SUCCESSFUL|EXECUTION SUCCESS|Sensor .*(Python|JavaScript|TypeScript|Cobertura|coverage)" "$OUT/scanner_$name.log" | cut -c1-160 || true
  "$PY" "$TEAM/sonar/sonar_admin.py" wait-task .scannerwork/report-task.txt
}

scan main
"$PY" "$TEAM/sonar/sonar_admin.py" export helpdesk "$OUT/main"

# complexity probe: only the business-rule files, analysed with the probe profile
RULE_FILES="helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py,helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py,helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py"
"$PY" "$TEAM/sonar/sonar_admin.py" probe-profile
"$PY" "$TEAM/sonar/sonar_admin.py" assign-profile helpdesk-complexity
scan complexity -Dsonar.projectKey=helpdesk-complexity \
  "-Dsonar.projectName=Helpdesk business-rule files (complexity probe)" \
  -Dsonar.sources=helpdesk -Dsonar.inclusions="$RULE_FILES" -Dsonar.tests= -Dsonar.test.inclusions=
"$PY" "$TEAM/sonar/sonar_admin.py" export helpdesk-complexity "$OUT/complexity"
"$PY" "$TEAM/sonar/summarise.py" "$OUT"
rm -rf .scannerwork
