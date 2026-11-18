#!/usr/bin/env bash
# Analyse cc_calibration.py with the complexity probe profile and list what
# SonarQube reports per function next to the textbook value.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TEAM="$(cd "$HERE/../.." && pwd)"
PY="$TEAM/../../../../env/bin/python"
SCANNER="${SCANNER:-$HOME/sonar/sonar-scanner/bin/sonar-scanner}"
export SONAR_URL="${SONAR_URL:-http://127.0.0.1:9100}"
set -a; . "$HOME/.sqe-env"; set +a
"$PY" "$TEAM/sonar/sonar_admin.py" probe-profile >/dev/null
"$PY" "$TEAM/sonar/sonar_admin.py" assign-profile sqe-cc-calibration
WORK="$(mktemp -d)"
cp "$HERE/cc_calibration.py" "$WORK/"
SONAR_TOKEN="$SONAR_TOKEN" "$SCANNER" -Dsonar.host.url="$SONAR_URL" \
  -Dsonar.projectKey=sqe-cc-calibration -Dsonar.projectBaseDir="$WORK" -Dsonar.sources=. \
  -Dsonar.working.directory="$WORK/.scannerwork" > "$HERE/scanner_calibration.log" 2>&1
"$PY" "$TEAM/sonar/sonar_admin.py" wait-task "$WORK/.scannerwork/report-task.txt"
"$PY" "$TEAM/sonar/sonar_admin.py" export sqe-cc-calibration "$HERE/export"
"$PY" - "$HERE" <<'EOF'
import json, re, sys
from pathlib import Path
here = Path(sys.argv[1])
src = (here / "cc_calibration.py").read_text().splitlines()
reported = {}
for issue in json.loads((here / "export/issues.json").read_text()):
    if issue["rule"] == "python:FunctionComplexity":
        reported[issue["line"]] = int(re.search(r"complexity of (\d+)", issue["message"]).group(1))
rows = ["| Function | Textbook (decisions + 1) | SonarQube | Construct counted by Sonar? |", "|---|---|---|---|"]
for number, line in enumerate(src, 1):
    m = re.match(r"def (\w+).*#\s*textbook (\d+)", line)
    if m:
        sonar = reported.get(number, 1)  # functions at 1 are not reported by the rule
        rows.append(f"| `{m.group(1)}` | {m.group(2)} | {sonar} | {'yes' if sonar == int(m.group(2)) else 'NO'} |")
(here / "calibration.md").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
EOF
rm -rf "$WORK"
