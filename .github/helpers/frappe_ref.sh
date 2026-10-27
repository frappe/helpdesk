#!/bin/bash
# Resolve a version-NN branch to its latest release tag; other refs pass through.
# Usage: frappe_ref.sh <ref> [repo]   e.g. frappe_ref.sh version-16
set -euo pipefail
ref="$1"
repo="${2:-frappe}"
if [[ "$ref" =~ ^version-([0-9]+)$ ]]; then
	major="${BASH_REMATCH[1]}"
	# A failed ls-remote exits here with git's own error; only an empty match falls through.
	tags=$(git ls-remote --tags --refs "https://github.com/frappe/${repo}" "v${major}.*")
	ref=$(sed 's#.*refs/tags/##' <<<"$tags" | grep -E "^v${major}\.[0-9]+\.[0-9]+$" | sort -V | tail -1 || true)
fi
[ -n "$ref" ] || { echo "No release found for $1 in frappe/${repo}" >&2; exit 1; }
echo "$ref"
