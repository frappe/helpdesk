#!/usr/bin/env bash
# Run the k6 workload with 1 and with 5 users, twice each, from the same
# starting data, and collect raw output, environment details and a summary.
# Usage (bench running): bash tests/team/perf/run_load.sh
set -uo pipefail
TEAM="$(cd "$(dirname "$0")/.." && pwd)"
BENCH="$(cd "$TEAM/../../../.." && pwd)"
K6="${K6:-$HOME/k6/k6}"
OUT="$TEAM/perf/evidence"
mkdir -p "$OUT"
set -a; . "$TEAM/.env"; set +a

{
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "machine: $(lscpu | sed -n 's/^Model name: *//p'), $(nproc) logical CPUs, $(free -m | awk '/Mem:/{print $2}') MB RAM (WSL2)"
  echo "os: $(lsb_release -ds 2>/dev/null), kernel $(uname -r)"
  echo "k6: $("$K6" version | head -1)"
  echo "python: $("$BENCH/env/bin/python" --version)"
  echo "frappe: $(git -C "$BENCH/apps/frappe" describe --tags --always) $(git -C "$BENCH/apps/frappe" rev-parse --short HEAD)"
  echo "helpdesk: $(git -C "$BENCH/apps/helpdesk" rev-parse --short HEAD) (baseline e326986 plus the team's uncommitted changes)"
  echo "mariadb: $(mariadb --version | sed -n 's/.*from \([^ ,]*\).*/\1/p')"
  echo "redis: $(redis-server --version | awk '{print $3}')"
  echo "web server: $(grep '^web:' "$BENCH/Procfile")  (Werkzeug development server)"
  echo "site: $SQE_SITE, developer_mode on"
} > "$OUT/environment.txt"
cat "$OUT/environment.txt"

for vus in 1 5; do
  for run in 1 2; do
    bash "$TEAM/seed.sh" reset >/dev/null
    sleep 5   # let the server settle after the reset
    name="vus${vus}_run${run}"
    "$K6" run --quiet \
      -e VUS="$vus" -e RUN="$run" -e BASE="$SQE_BASE_URL" \
      -e CUSTOMER_EMAIL="$SQE_CUSTOMER_A_EMAIL" -e CUSTOMER_PASSWORD="$SQE_CUSTOMER_A_PASSWORD" \
      -e AGENT_EMAIL="$SQE_AGENT_EMAIL" -e AGENT_PASSWORD="$SQE_AGENT_PASSWORD" \
      -e OUT="$OUT/$name.json" \
      --out "json=$OUT/$name.raw.json.gz" \
      "$TEAM/perf/read_ticket.js" 2>&1 | tee "$OUT/$name.log"
    echo "k6 exit code: ${PIPESTATUS[0]} (99 = a limit was exceeded)" | tee -a "$OUT/$name.log"
  done
done
bash "$TEAM/seed.sh" reset >/dev/null
"$BENCH/env/bin/python" "$TEAM/perf/summarise.py" "$OUT"
