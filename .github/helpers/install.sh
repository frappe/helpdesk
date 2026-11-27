#!/bin/bash

set -eo pipefail

export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"
export UV_PYTHON="${UV_PYTHON:-3.14}"
printf '%s\n' "$HOME/pilot/bin" "$HOME/.local/bin" >> "$GITHUB_PATH"

curl -fsSL https://raw.githubusercontent.com/frappe/pilot/develop/install.sh | sh -s -- --ci

pilot new frappe-bench --frappe-branch "${FRAPPE_BRANCH:-develop}"
pilot -b frappe-bench set-bench-config python "3.14"
pilot -b frappe-bench set-bench-config admin_allow_site_to_pilot_communication false
pilot -b frappe-bench set-bench-config mariadb_existing true
pilot -b frappe-bench set-bench-config mariadb_host 127.0.0.1
pilot -b frappe-bench set-bench-config mariadb_port 3306
pilot -b frappe-bench set-bench-config mariadb_admin_user root
pilot -b frappe-bench set-bench-config mariadb_password root
pilot -b frappe-bench init --skip-frontend

# Ubuntu 26.04's mariadb-client (11.8) requires SSL; container MariaDB has none.
printf '[client]\nskip-ssl\n' > ~/.my.cnf
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

cd "$HOME/pilot/benches/frappe-bench" || exit 1

uv pip install --python env/bin/python -e "apps/frappe[test]"
pilot get-app https://github.com/frappe/erpnext --branch "${FRAPPE_BRANCH:-develop}" --skip-assets
pilot get-app https://github.com/frappe/telephony --skip-assets
pilot get-app "$GITHUB_WORKSPACE" --branch "$GITHUB_SHA" --skip-assets

pilot -b frappe-bench start > "$RUNNER_TEMP/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
  http://127.0.0.1:7000/api/v1/health

pilot new-site test_site --admin-password admin --apps frappe erpnext telephony helpdesk --skip-assets
mkdir -p sites/assets && echo '{}' > sites/assets/assets.json

pilot frappe --site test_site set-config allow_tests true
pilot frappe --site test_site set-config host_name "http://test_site:8000"
pilot frappe --site test_site set-config -p throttle_user_limit 100
pilot frappe --site test_site set-config auto_email_id "test@example.com"
pilot frappe --site test_site set-config mail_server "smtp.example.com"
pilot frappe --site test_site set-config mail_login "test@example.com"
pilot frappe --site test_site set-config mail_password "test"
