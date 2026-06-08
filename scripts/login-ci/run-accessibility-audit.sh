#!/bin/bash
# Accessibility Audit for Login Page
# Sprint 6: WCAG 2.1 AA compliance check

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_URL="${SITE_URL:-http://localhost:8000}"
LOGIN_URL="${SITE_URL}/login_preview"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Helpdesk Login - Accessibility Audit (WCAG 2.1 AA)      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if axe-core CLI is installed
if ! command -v axe &> /dev/null; then
    echo "⚠️  axe-core CLI not found. Installing..."
    npm install -g @axe-core/cli
fi

echo "🔍 Running axe accessibility scan..."
echo "   URL: ${LOGIN_URL}"
echo ""

# Run axe scan
axe "${LOGIN_URL}" \
    --exit \
    --tags wcag2a,wcag2aa,wcag21a,wcag21aa,best-practice \
    --disable color-contrast-enhanced \
    --reporter json \
    --save "${SCRIPT_DIR}/a11y-report.json" \
    || true

# Check if report exists
if [ ! -f "${SCRIPT_DIR}/a11y-report.json" ]; then
    echo "❌ Accessibility scan failed - no report generated"
    exit 1
fi

# Parse results
VIOLATIONS=$(jq '.violations | length' "${SCRIPT_DIR}/a11y-report.json")
PASSES=$(jq '.passes | length' "${SCRIPT_DIR}/a11y-report.json")
INCOMPLETE=$(jq '.incomplete | length' "${SCRIPT_DIR}/a11y-report.json")

echo "════════════════════════════════════════════════════════════"
echo "Results:"
echo "  ✅ Passes:     ${PASSES}"
echo "  ⚠️  Incomplete: ${INCOMPLETE}"
echo "  ❌ Violations: ${VIOLATIONS}"
echo "════════════════════════════════════════════════════════════"
echo ""

# Show violations if any
if [ "$VIOLATIONS" -gt 0 ]; then
    echo "⚠️  WCAG Violations Found:"
    echo ""
    jq -r '.violations[] | "  • \(.id) (\(.impact))\n    \(.description)\n    Nodes affected: \(.nodes | length)\n"' \
        "${SCRIPT_DIR}/a11y-report.json"
    echo ""
    echo "📄 Full report saved: ${SCRIPT_DIR}/a11y-report.json"
    exit 1
else
    echo "✅ All WCAG 2.1 AA checks passed!"
    echo "📄 Report saved: ${SCRIPT_DIR}/a11y-report.json"
    exit 0
fi
