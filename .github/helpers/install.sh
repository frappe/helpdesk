#!/bin/bash

set -e

cd ~ || ex

sudo apt update
sudo apt remove mysql-server mysql-client
sudo apt install libcups2-dev redis-server mariadb-client-10.6

pip install frappe-bench

git clone "https://github.com/frappe/frappe" --branch "develop" --depth 1
bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

mkdir ~/frappe-bench/sites/test_site

cp -r "${GITHUB_WORKSPACE}/.github/helpers/site_config_mariadb.json" ~/frappe-bench/sites/test_site/site_config.json

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER 'test_frappe'@'localhost' IDENTIFIED BY 'test_frappe'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE DATABASE test_frappe"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO 'test_frappe'@'localhost'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

install_whktml() {
	if [ "$(lsb_release -rs)" = "22.04" ]; then
		wget -O /tmp/wkhtmltox.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
		sudo apt install /tmp/wkhtmltox.deb
	else
		echo "Please update this script to support wkhtmltopdf for $(lsb_release -ds)"
		exit 1
	fi
}
install_whktml &
wkpid=$!


cd ~/frappe-bench || exit

sed -i 's/watch:/# watch:/g' Procfile
sed -i 's/schedule:/# schedule:/g' Procfile
sed -i 's/socketio:/# socketio:/g' Procfile
sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

bench get-app helpdesk "${GITHUB_WORKSPACE}"
bench setup requirements --dev

wait $wkpid

bench start &> bench_run_logs.txt &
CI=Yes bench build --app frappe &
bench --site test_site reinstall --yes
