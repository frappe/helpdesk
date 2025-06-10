#!/bin/bash

set -e

cd ~ || ex

sudo apt update
sudo apt remove mysql-server mysql-client
sudo apt install libcups2-dev redis-server mariadb-client libmariadb-dev

pip install frappe-bench
HD_BRANCH=${HD_BRANCH:-"develop"}
FRAPPE_BRANCH=${FRAPPE_BRANCH:-"develop"}
# if HD BRANCH IS Develop, then FRAPPE_BRANCH should also be develop
if [ "${HD_BRANCH}" = "develop" ]; then
    FRAPPE_BRANCH="develop"
# if HD BRANCH is Main, then FRAPPE_BRANCH should also be main
elif [ "${HD_BRANCH}" = "main" ]; then
    FRAPPE_BRANCH="version-15"
fi
echo "Installing Frappe Framework"
echo "Branch: ${FRAPPE_BRANCH}"
git clone "https://github.com/frappe/frappe" --branch ${FRAPPE_BRANCH} --depth 1 
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

echo "Installing Helpdesk App"
echo "Branch: ${HD_BRANCH}"
echo "Installing from ${GITHUB_WORKSPACE}"

bench get-app helpdesk --branch "${HD_BRANCH}" 
bench setup requirements --dev


bench start &>> ~/frappe-bench/bench_start.log &
CI=Yes bench build --app frappe &
bench --site test_site reinstall --yes
