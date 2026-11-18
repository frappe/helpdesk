#!/usr/bin/env bash
# Start / stop / check the local SonarQube Community Build (~/sonar/sonarqube).
# Usage: bash tests/team/sonar/server.sh start|stop|status
set -euo pipefail
HOME_SQ="${SONAR_HOME:-$HOME/sonar/sonarqube}"
URL="${SONAR_URL:-http://127.0.0.1:9100}"
case "${1:-status}" in
  start)
    # sonar.sh exits non-zero when already running, so only start it if it is not
    "$HOME_SQ/bin/linux-x86-64/sonar.sh" status >/dev/null || "$HOME_SQ/bin/linux-x86-64/sonar.sh" start
    for _ in $(seq 1 120); do
      # not reachable while it boots: treat as "not up yet" and keep waiting
      body=$(curl -s -m 5 "$URL/api/system/status") || body=""
      status=$(echo "$body" | sed -n 's/.*"status":"\([A-Z_]*\)".*/\1/p')
      [ "$status" = "UP" ] && { echo "SonarQube is UP at $URL"; exit 0; }
      sleep 5
    done
    echo "SonarQube did not come up; see $HOME_SQ/logs/"; exit 1 ;;
  stop) "$HOME_SQ/bin/linux-x86-64/sonar.sh" stop ;;
  status) curl -s -m 5 "$URL/api/system/status"; echo ;;
esac
