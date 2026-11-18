#!/usr/bin/env bash
# Open-source dependency audit of the Python environment the site runs on.
# Records exactly which packages and versions were checked, then runs
# pip-audit (PyPA, OSV/PyPI advisory database) against that pinned list.
# Usage: bash tests/team/security/dependency_audit.sh
set -uo pipefail
TEAM="$(cd "$(dirname "$0")/.." && pwd)"
BENCH="$(cd "$TEAM/../../../.." && pwd)"
OUT="$TEAM/security/evidence/dependencies"
mkdir -p "$OUT"
export PATH="$HOME/.local/bin:$PATH"

echo "pip-audit: $(pip-audit --version)" | tee "$OUT/tool_versions.txt"
echo "python: $("$BENCH/env/bin/python" --version)" | tee -a "$OUT/tool_versions.txt"
date -u +"run: %Y-%m-%dT%H:%M:%SZ" | tee -a "$OUT/tool_versions.txt"

# every package installed in the bench environment, with its version
uv pip freeze --python "$BENCH/env/bin/python" > "$OUT/installed_packages.txt"
# the three apps are installed from local checkouts: list them separately
grep -E '^(-e |.* @ file://)' "$OUT/installed_packages.txt" > "$OUT/local_apps.txt"
grep -v -E '^(-e |.* @ file://)' "$OUT/installed_packages.txt" > "$OUT/audited_requirements.txt"
echo "packages checked: $(wc -l < "$OUT/audited_requirements.txt") (+ $(wc -l < "$OUT/local_apps.txt") local apps)"

pip-audit --requirement "$OUT/audited_requirements.txt" --no-deps --disable-pip \
  --format json --output "$OUT/pip_audit.json" --progress-spinner off
AUDIT_EXIT=$?
pip-audit --requirement "$OUT/audited_requirements.txt" --no-deps --disable-pip \
  --format markdown --output "$OUT/pip_audit.md" --progress-spinner off --desc
echo "pip-audit exit code: $AUDIT_EXIT (1 = vulnerabilities found)"
exit 0
