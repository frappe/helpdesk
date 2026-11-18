#!/usr/bin/env bash
# Build the final report PDF.   Usage: bash tests/team/report/build.sh [OUT.pdf]
#
# One-time set-up (a separate environment, so the bench is not touched):
#   uv venv ~/report-venv
#   uv pip install --python ~/report-venv/bin/python reportlab svglib matplotlib markdown-it-py pyyaml
#   sudo apt-get install graphviz
# Fill in report/meta.yaml (names, roll numbers, section) first.
set -euo pipefail
TEAM="$(cd "$(dirname "$0")/.." && pwd)"
PY="${REPORT_PYTHON:-$HOME/report-venv/bin/python}"
OUT="${1:-$TEAM/report/report.pdf}"
"$PY" "$TEAM/tools/build_report.py" "$OUT"
