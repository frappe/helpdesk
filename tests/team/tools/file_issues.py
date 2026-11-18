"""File the defect log (management/defects.yaml) as GitHub Issues on the
group's fork, with severity / priority / status / triage labels.

Dry run (default) prints what would be created. To create them:
    python tools/file_issues.py --repo OWNER/helpdesk --execute
Needs the GitHub CLI (`gh auth login` done by a team member). Numbers of
created issues are written to management/issue_map.json; put them into
the `issue:` field of defects.yaml afterwards. Defects that already have an
issue number, or are in issue_map.json, are skipped, so reruns are safe.
"""

import argparse
import json
import subprocess
from pathlib import Path

import yaml

MGMT = Path(__file__).resolve().parents[1] / "management"
MAP = MGMT / "issue_map.json"

LABELS = {
    "severity: Critical": "b60205", "severity: Major": "d93f0b",
    "severity: Minor": "fbca04", "severity: Trivial": "c2e0c6",
    "priority: P1": "b60205", "priority: P2": "d93f0b", "priority: P3": "fbca04", "priority: P4": "c2e0c6",
}


def body(d):
    lines = [f"**Defect ID:** {d['id']} (ref {d['ref']})", "",
             "| Field | Value |", "|---|---|",
             f"| Severity | {d['severity']} |", f"| Priority | {d['priority']} |",
             f"| Status | {d['status']} |", f"| Triage decision | {d['triage']} |",
             f"| Category | {d['category']} |", f"| Layer | {d['layer']} |",
             f"| Risk | {', '.join(d.get('risk', [])) or '-'} |",
             f"| Found by | {d.get('found_by', '-')} |", f"| Found on | {d.get('found_on', '-')} |",
             f"| Root-cause file | `{d.get('file', '-')}` |"]
    if d.get("note"):
        lines.append(f"| Note | {d['note']} |")
    for key, title in (("steps", "Steps to reproduce"), ("expected", "Expected"), ("actual", "Actual")):
        if d.get(key):
            lines += ["", f"### {title}", "", str(d[key]).strip()]
    if d.get("rca"):
        lines += ["", f"Root cause analysis: `tests/team/management/{d['rca']}`"]
    lines += ["", "Baseline: frappe/helpdesk e326986 on frappe v16.56.0. Logged from tests/team/management/defects.yaml."]
    return "\n".join(lines)


def labels(d):
    status = "status: " + d["status"].split(" (")[0]
    triage = "triage: " + d["triage"]
    return [f"severity: {d['severity']}", f"priority: {d['priority']}", status, triage, "category: " + d["category"]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="OWNER/NAME of the group's public fork")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    defects = yaml.safe_load((MGMT / "defects.yaml").read_text())
    done = json.loads(MAP.read_text()) if MAP.exists() else {}
    todo = [d for d in defects if not d.get("issue") and d["id"] not in done]
    if args.execute:
        if not args.repo:
            raise SystemExit("--repo is required with --execute")
        wanted = {l for d in todo for l in labels(d)}
        for name in sorted(wanted):
            subprocess.run(["gh", "label", "create", name, "--repo", args.repo, "--force",
                            "--color", LABELS.get(name, "ededed")], check=True, capture_output=True)
    for d in todo:
        title = f"[{d['id']}] {d['title']}"
        if not args.execute:
            print(f"would create: {title}  labels={labels(d)}")
            continue
        cmd = ["gh", "issue", "create", "--repo", args.repo, "--title", title, "--body", body(d)]
        for l in labels(d):
            cmd += ["--label", l]
        url = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()
        done[d["id"]] = url
        MAP.write_text(json.dumps(done, indent=1))
        if d["status"] in ("Rejected",):
            subprocess.run(["gh", "issue", "close", url, "--reason", "not planned"], check=True)
        print(f"created {url}  {title}")
    print(f"{len(todo)} defects {'filed' if args.execute else 'to file'}")


if __name__ == "__main__":
    main()
