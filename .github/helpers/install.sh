#!/bin/bash

set -e

cd ~ || exit

# Install system deps (apt) in the background while installing the bench tool
# via uv -- the two share no inputs, so overlap them.
install_system_deps() {
    sudo apt update
    sudo apt remove -y mysql-server mysql-client
    sudo apt install -y libcups2-dev redis-server mariadb-client libmariadb-dev
}
install_system_deps &> ~/system_deps.log &
sys_pid=$!

uv tool install frappe-bench
export PATH="${HOME}/.local/bin:${PATH}"
[ -n "${GITHUB_PATH}" ] && echo "${HOME}/.local/bin" >> "${GITHUB_PATH}"

if ! wait "$sys_pid"; then
    echo "System dependency install failed:"
    cat ~/system_deps.log
    exit 1
fi

git clone "https://github.com/frappe/frappe" --branch "develop" --depth 1

# ERPNext clone is independent of bench init -- run it in the background.
git clone "https://github.com/frappe/erpnext" --branch "develop" --depth 1 &> ~/erpnext_clone.log &
erpnext_pid=$!

bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

mkdir ~/frappe-bench/sites/test_site

cp -r "${GITHUB_WORKSPACE}/.github/helpers/site_config_mariadb.json" ~/frappe-bench/sites/test_site/site_config.json

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

# Ephemeral CI database: trade crash-safety for far fewer fsyncs.
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL innodb_flush_log_at_trx_commit = 0"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL sync_binlog = 0"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER 'test_frappe'@'localhost' IDENTIFIED BY 'test_frappe'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE DATABASE test_frappe"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO 'test_frappe'@'localhost'"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

install_whktml() {
    wget -O /tmp/wkhtmltox.tar.xz https://github.com/frappe/wkhtmltopdf/raw/master/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
    tar -xf /tmp/wkhtmltox.tar.xz -C /tmp
    sudo mv /tmp/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
    sudo chmod o+x /usr/local/bin/wkhtmltopdf
}
install_whktml &

cd ~/frappe-bench || exit

sed -i 's/watch:/# watch:/g' Procfile
sed -i 's/schedule:/# schedule:/g' Procfile
sed -i 's/socketio:/# socketio:/g' Procfile
sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

if ! wait "$erpnext_pid"; then
    echo "ERPNext clone failed:"
    cat ~/erpnext_clone.log
    exit 1
fi

bench get-app erpnext ~/erpnext
bench get-app telephony
bench get-app helpdesk "${GITHUB_WORKSPACE}"
bench setup requirements --dev


bench start &>> ~/frappe-bench/bench_start.log &
CI=Yes bench build --app frappe &
bench --site test_site reinstall --yes

bench --verbose --site test_site install-app erpnext
bench --verbose --site test_site install-app telephony
bench --verbose --site test_site install-app helpdesk
