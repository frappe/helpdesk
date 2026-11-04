#!/bin/bash
# Sets FRAPPE_BRANCH and PYTHON_VERSION for the helpdesk branch passed as $1.

case "$1" in
	version-15 | version-15-hotfix) frappe=version-15 python=3.12 ;;
	version-16 | version-16-hotfix) frappe=version-16 python=3.14 ;;
	*) frappe=develop python=3.14 ;;
esac

echo "FRAPPE_BRANCH=$frappe" >>"$GITHUB_ENV"
echo "PYTHON_VERSION=$python" >>"$GITHUB_ENV"
