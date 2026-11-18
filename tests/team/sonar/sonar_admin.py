"""Small SonarQube Web API helper for the team's local server.

Commands:
  init            first start: replace the default admin password, create an
                  analysis token, and store both in ~/.sqe-env (never printed)
  probe-profile   create the "SQE complexity probe" Python quality profile:
                  function cyclomatic complexity (S1541) and cognitive
                  complexity (S3776) with threshold 1, so every function above 1
                  is reported with its exact value
  wait-task FILE  wait for the background task of an analysis (report-task.txt)
  export KEY DIR  save measures, issues, hotspots and gate status as JSON
  gate            create the "SQE gate" quality gate and make it the default
  check-gate KEY  print the gate result per condition; exit 1 if it failed

Server: SONAR_URL (default http://127.0.0.1:9100).
"""

import json
import os
import secrets
import string
import sys
import time
from pathlib import Path

import requests

URL = os.environ.get("SONAR_URL", "http://127.0.0.1:9100")
ENV_FILE = Path.home() / ".sqe-env"
PROBE_PROFILE = "SQE complexity probe"

METRICS = [
    "ncloc", "lines", "files", "functions", "classes", "statements",
    "complexity", "cognitive_complexity",
    "bugs", "vulnerabilities", "code_smells", "security_hotspots",
    "reliability_rating", "security_rating", "sqale_rating", "security_review_rating",
    "sqale_index", "sqale_debt_ratio",
    "duplicated_lines_density", "duplicated_blocks", "duplicated_lines",
    "coverage", "line_coverage", "branch_coverage", "lines_to_cover",
    "uncovered_lines", "conditions_to_cover", "uncovered_conditions",
    "comment_lines_density", "tests", "test_failures", "test_errors",
    "alert_status",
]


def read_env():
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def save_env(key, value):
    lines = [l for l in ENV_FILE.read_text().splitlines() if not l.startswith(f"{key}=")] if ENV_FILE.exists() else []
    lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n")
    ENV_FILE.chmod(0o600)


def session():
    env = read_env()
    s = requests.Session()
    s.auth = ("admin", env.get("SONAR_ADMIN_PASSWORD", "admin"))
    return s


def call(s, method, path, **params):
    r = s.request(method, f"{URL}{path}", params=params if method == "GET" else None,
                  data=params if method != "GET" else None, timeout=60)
    if r.status_code >= 400:
        raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text and r.headers.get("content-type", "").startswith("application/json") else {}


def new_password():
    alphabet = string.ascii_letters + string.digits
    core = "".join(secrets.choice(alphabet) for _ in range(20))
    return f"Sqe-{core}-9a!"  # upper, lower, digit and special characters


def init():
    env = read_env()
    if "SONAR_ADMIN_PASSWORD" not in env:
        password = new_password()
        s = requests.Session()
        s.auth = ("admin", "admin")
        call(s, "POST", "/api/users/change_password", login="admin",
             previousPassword="admin", password=password)
        save_env("SONAR_ADMIN_PASSWORD", password)
        print("admin password replaced and stored in ~/.sqe-env")
    s = session()
    if "SONAR_TOKEN" not in read_env():
        name = f"sqe-analysis-{int(time.time())}"
        token = call(s, "POST", "/api/user_tokens/generate", name=name)["token"]
        save_env("SONAR_TOKEN", token)
        print(f"analysis token '{name}' created and stored in ~/.sqe-env")
    print("server version:", requests.get(f"{URL}/api/server/version", timeout=10).text)


def probe_profile():
    s = session()
    profiles = call(s, "GET", "/api/qualityprofiles/search", language="py")["profiles"]
    existing = [p for p in profiles if p["name"] == PROBE_PROFILE]
    key = existing[0]["key"] if existing else call(
        s, "POST", "/api/qualityprofiles/create", language="py", name=PROBE_PROFILE)["profile"]["key"]
    for rule in ("python:FunctionComplexity", "python:S3776"):
        params = call(s, "GET", "/api/rules/show", key=rule)["rule"].get("params", [])
        names = [p["key"] for p in params]
        print(f"{rule} params: {names}")
        threshold_param = next(n for n in names if "hreshold" in n or n.lower() == "max")
        call(s, "POST", "/api/qualityprofiles/activate_rule", key=key, rule=rule,
             params=f"{threshold_param}=1")
        print(f"activated {rule} with {threshold_param}=1 in '{PROBE_PROFILE}'")


def assign_profile(project):
    """Create the probe project if needed and give it the probe profile."""
    s = session()
    found = call(s, "GET", "/api/projects/search", projects=project)["components"]
    if not found:
        call(s, "POST", "/api/projects/create", project=project,
             name="Helpdesk business-rule files (complexity probe)")
    call(s, "POST", "/api/qualityprofiles/add_project", language="py",
         qualityProfile=PROBE_PROFILE, project=project)
    print(f"project {project} uses '{PROBE_PROFILE}' for Python")


def wait_task(report_file):
    props = dict(l.split("=", 1) for l in Path(report_file).read_text().splitlines() if "=" in l)
    s = session()
    for _ in range(180):
        task = call(s, "GET", "/api/ce/task", id=props["ceTaskId"])["task"]
        if task["status"] in ("SUCCESS", "FAILED", "CANCELED"):
            print(f"analysis task {task['status']} ({task.get('executionTimeMs', '?')} ms)")
            return 0 if task["status"] == "SUCCESS" else 1
        time.sleep(2)
    print("analysis task did not finish in 6 minutes")
    return 1


def paged(s, path, key, **params):
    items, page = [], 1
    while True:
        data = call(s, "GET", path, p=page, ps=500, **params)
        items += data[key]
        total = data.get("paging", {}).get("total", data.get("total", 0))
        if page * 500 >= total or page * 500 >= 10000:
            return items
        page += 1


def export(project, out_dir):
    s = session()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    measures = call(s, "GET", "/api/measures/component", component=project,
                    metricKeys=",".join(METRICS))
    (out / "measures.json").write_text(json.dumps(measures, indent=1))
    files = paged(s, "/api/measures/component_tree", "components", component=project,
                  qualifiers="FIL", metricKeys="ncloc,complexity,cognitive_complexity,coverage,functions,"
                  "lines_to_cover,uncovered_lines,conditions_to_cover,uncovered_conditions,"
                  "bugs,vulnerabilities,code_smells")
    (out / "files.json").write_text(json.dumps(files, indent=1))
    issues = paged(s, "/api/issues/search", "issues", components=project)
    (out / "issues.json").write_text(json.dumps(issues, indent=1))
    hotspots = paged(s, "/api/hotspots/search", "hotspots", project=project)
    (out / "hotspots.json").write_text(json.dumps(hotspots, indent=1))
    gate = call(s, "GET", "/api/qualitygates/project_status", projectKey=project)
    (out / "quality_gate.json").write_text(json.dumps(gate, indent=1))
    analyses = call(s, "GET", "/api/project_analyses/search", project=project)
    (out / "analyses.json").write_text(json.dumps(analyses, indent=1))
    print(f"exported {project}: {len(files)} files, {len(issues)} issues, {len(hotspots)} hotspots -> {out}")


SQE_GATE = "SQE gate"
# Conditions on overall code. The CI server is created fresh for every run, so
# there is no "new code" period to compare with; instead each count is held at
# its value in the baseline analysis of 18 Nov 2026 (ratchet: no worse than the
# baseline). Ratings: 1 = A ... 5 = E.
GATE_CONDITIONS = [
    ("reliability_rating", "4", "reliability no worse than D (baseline D)"),
    ("security_rating", "4", "security no worse than D (baseline D)"),
    ("sqale_rating", "1", "maintainability A (baseline A)"),
    ("bugs", "122", "bugs no more than the baseline 122"),
    ("vulnerabilities", "8", "vulnerabilities no more than the baseline 8"),
    ("security_review_rating", "1", "security review A, i.e. no unreviewed hotspots (baseline 0 hotspots)"),
    ("duplicated_lines_density", "3", "duplication at most 3 % (baseline 1.6 %)"),
    ("test_failures", "0", "no failing unit tests in the imported report"),
    ("test_errors", "0", "no erroring unit tests in the imported report"),
]


def gate():
    """Create (or reset) the SQE quality gate and make it the default."""
    s = session()
    gates = call(s, "GET", "/api/qualitygates/list")["qualitygates"]
    if not any(g["name"] == SQE_GATE for g in gates):
        call(s, "POST", "/api/qualitygates/create", name=SQE_GATE)
    for condition in call(s, "GET", "/api/qualitygates/show", name=SQE_GATE).get("conditions", []):
        call(s, "POST", "/api/qualitygates/delete_condition", id=condition["id"])
    for metric, error, meaning in GATE_CONDITIONS:
        call(s, "POST", "/api/qualitygates/create_condition", gateName=SQE_GATE,
             metric=metric, op="GT", error=error)
        print(f"condition: {metric} > {error} fails ({meaning})")
    call(s, "POST", "/api/qualitygates/set_as_default", name=SQE_GATE)
    print(f"'{SQE_GATE}' is the default quality gate")


def check_gate(project):
    """Print the gate result per condition; exit 1 if the gate failed."""
    status = call(session(), "GET", "/api/qualitygates/project_status", projectKey=project)["projectStatus"]
    rows = [f"| {c['metricKey']} | {c.get('actualValue', '-')} | > {c.get('errorThreshold', '-')} | {c['status']} |"
            for c in status.get("conditions", [])]
    report = "\n".join([f"### SonarQube quality gate ({project}): {status['status']}", "",
                        "| Metric | Actual | Fails when | Status |", "|---|---|---|---|", *rows, ""])
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write(report + "\n")
    return 0 if status["status"] == "OK" else 1


if __name__ == "__main__":
    command, *rest = sys.argv[1:] or ["help"]
    if command == "gate":
        gate()
    elif command == "check-gate":
        sys.exit(check_gate(rest[0]))
    elif command == "init":
        init()
    elif command == "probe-profile":
        probe_profile()
    elif command == "assign-profile":
        assign_profile(rest[0])
    elif command == "wait-task":
        sys.exit(wait_task(rest[0]))
    elif command == "export":
        export(rest[0], rest[1])
    else:
        print(__doc__)
