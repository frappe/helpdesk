# SE3002 SQE project: team tests for Frappe Helpdesk

Everything the team wrote lives in this folder. Upstream tests are not ours
and earn no marks.

## System under test

| | |
|---|---|
| Upstream | https://github.com/frappe/helpdesk (licence AGPL-3.0) |
| Baseline | branch `version-16`, commit `e326986329341c803dd4bf094322670ad0591ca5` (Helpdesk 16.1.0) |
| Framework | https://github.com/frappe/frappe `version-16`, v16.56.0 (`49789a1`) |
| Also installed | https://github.com/frappe/telephony (`9447577`), a Helpdesk dependency |
| Module and workflows | Ticket module: A raise a ticket, B handle and close a ticket (see `management/TEST_PLAN.md`) |

## Install (Ubuntu 26.04 on WSL2; any Ubuntu with Python 3.14 works)

System packages: MariaDB 11.8, Redis 8, `git`, `pipx`, build tools. Then:

```bash
# Node 24 + yarn
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
. ~/.nvm/nvm.sh && nvm install 24 && npm install -g yarn
# bench and uv
pipx install frappe-bench && pipx install uv
# bench, framework and apps at the baseline
bench init --frappe-branch version-16 --skip-redis-config-generation ~/frappe-bench
cd ~/frappe-bench && bench setup redis
bench get-app https://github.com/frappe/telephony
bench get-app --branch version-16 https://github.com/frappe/helpdesk
git -C apps/helpdesk checkout e326986329341c803dd4bf094322670ad0591ca5
# site (DB root password and admin password are local test values you choose)
bench new-site helpdesk.localhost --db-root-username root --admin-password <admin>
bench --site helpdesk.localhost install-app telephony
bench --site helpdesk.localhost install-app helpdesk
bench --site helpdesk.localhost set-config allow_tests true
bench --site helpdesk.localhost set-config developer_mode 1
bench use helpdesk.localhost
```

If the generated `Procfile` has no Redis lines, add:

```
redis_cache: redis-server config/redis_cache.conf
redis_queue: redis-server config/redis_queue.conf
```

## Start, seed, reset

```bash
cd ~/frappe-bench && bench start          # site on http://helpdesk.localhost:8000
bash apps/helpdesk/tests/team/seed.sh seed     # test accounts + settings, writes tests/team/.env
bash apps/helpdesk/tests/team/seed.sh reset    # delete test tickets, restore settings (run before each suite)
```

`seed` creates `agent.one@sqe.test` (Agent), `customer.a@sqe.test` and
`customer.b@sqe.test` (HD Customer). Their passwords are generated into
`tests/team/.env`, which is git-ignored. Python and Node clients call
`http://127.0.0.1:8000` with `Host: helpdesk.localhost`.

## Run the tests (from `~/frappe-bench/apps/helpdesk`)

| Activity | Command | Report |
|---|---|---|
| Unit + coverage gate | `bash tests/team/run_unit.sh` | `unit/README.md`, `reports/unit/` |
| Mutation | `bash tests/team/run_mutation.sh 95` | `mutation/SURVIVORS.md` |
| API (regenerates data first) | `bash tests/team/run_api.sh` | `api/WEAKNESSES.md` |
| Data generator / constraint change | `python tests/team/api/generate_testdata.py`; `bash tests/team/api/demo_constraint_change.sh` | `api/evidence/` |
| Use cases, usability, security (Playwright) | `bash tests/team/run_e2e.sh` | `e2e/USE_CASES.md`, `security/SECURITY_REPORT.md` |
| Accessibility scans | `cd tests/team/e2e && node a11y/scan.mjs before\|after` | `a11y/A11Y_REPORT.md` |
| ZAP passive / dependency audit | `bash tests/team/security/zap_passive.sh`; `bash tests/team/security/dependency_audit.sh` | `security/evidence/` |
| Performance | `bash tests/team/perf/run_load.sh` | `perf/PERFORMANCE_REPORT.md` |
| SonarQube | `bash tests/team/sonar/server.sh start`; `bash tests/team/sonar/run_sonar.sh` | `sonar/SONAR_REPORT.md` |
| Defect summary, Pareto, GQM | `python tests/team/tools/defects_report.py` | `management/generated/` |

## Tool versions

pytest 9.2, coverage.py 7.17.3, Cosmic Ray 8.9.0, Playwright 1.65.1
(Chromium), @axe-core/playwright 4.14.0, Lighthouse 13.6.0, OWASP ZAP 2.17.0
(Java 21), pip-audit 2.10.1, Grafana k6 2.4.0, SonarQube Community Build
26.11.0 + SonarScanner CLI 8.4.0, Python 3.14.4, Node 24, MariaDB 11.8.6,
Redis 8.0.5.

## Layout

| Folder | Content |
|---|---|
| `seed/`, `seed.sh` | synthetic data, seed and reset |
| `unit/`, `tools/scoped_coverage.py` | white-box unit tests, scoped coverage gate |
| `mutation/` | Cosmic Ray config, custom operators, survivor analysis |
| `api/` | OpenAPI spec, generator, generated data, API and recovery tests |
| `e2e/` | Playwright: use cases, usability tasks, security checks, a11y scans |
| `a11y/`, `security/`, `perf/`, `sonar/` | reports and evidence per activity |
| `management/` | test plan, estimation, risk register, traceability, defect log, RCA, progress, completion report |
