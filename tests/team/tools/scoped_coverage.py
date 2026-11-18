"""Check statement and branch coverage of the business-rule scope only.

coverage.py measures whole files. Our unit-test scope is two whole files plus
four named functions inside the 1,500-line hd_ticket.py, so this script reads
coverage.py's JSON report (which carries per-function regions) and reports the
figures for exactly that scope. It exits non-zero if anything in scope is
below the threshold, which lets CI use it as a gate.

Usage: python scoped_coverage.py coverage.json [--threshold 100]
"""

import argparse
import json
import sys

TICKET = "helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py"
CONTROLLER = "helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py"
STATUS = "helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py"

# file suffix -> functions in scope, or None for the whole file
SCOPE = {
    CONTROLLER: None,
    STATUS: None,
    TICKET: [
        "HDTicket.validate_feedback",
        "HDTicket.is_valid_status_transition",
        "HDTicket.set_resolution_date",
        "close_tickets_after_n_days",
    ],
}


def find_file(files, suffix):
    for path, data in files.items():
        if path.replace("\\", "/").endswith(suffix):
            return data
    raise SystemExit(f"not measured: {suffix} (was it passed to --cov?)")


def summarise(name, region):
    s = region["summary"]
    return {
        "name": name,
        "statements": s["num_statements"],
        "missed": s["missing_lines"],
        "branches": s.get("num_branches", 0),
        "missed_branches": s.get("missing_branches", 0),
        "missing_lines": region.get("missing_lines", []),
        "missing_branch_pairs": region.get("missing_branches", []),
    }


def pct(total, missed):
    return 100.0 if total == 0 else 100.0 * (total - missed) / total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--threshold", type=float, default=100.0)
    args = parser.parse_args()

    with open(args.report) as handle:
        files = json.load(handle)["files"]

    rows = []
    for suffix, functions in SCOPE.items():
        data = find_file(files, suffix)
        short = suffix.rsplit("/", 1)[-1]
        if functions is None:
            rows.append(summarise(f"{short} (whole file)", data))
            continue
        for function in functions:
            if function not in data["functions"]:
                raise SystemExit(f"function not found in {short}: {function}")
            rows.append(summarise(f"{short}::{function}", data["functions"][function]))

    print(f"{'scope item':<62}{'stmts':>6}{'miss':>6}{'stmt%':>8}{'br':>5}{'miss':>6}{'br%':>8}")
    failed = False
    totals = [0, 0, 0, 0]
    for row in rows:
        statement_pct = pct(row["statements"], row["missed"])
        branch_pct = pct(row["branches"], row["missed_branches"])
        totals[0] += row["statements"]
        totals[1] += row["missed"]
        totals[2] += row["branches"]
        totals[3] += row["missed_branches"]
        print(
            f"{row['name']:<62}{row['statements']:>6}{row['missed']:>6}{statement_pct:>8.1f}"
            f"{row['branches']:>5}{row['missed_branches']:>6}{branch_pct:>8.1f}"
        )
        if row["missing_lines"]:
            print(f"    missing lines: {row['missing_lines']}")
        if row["missing_branch_pairs"]:
            print(f"    missing branches: {row['missing_branch_pairs']}")
        if statement_pct < args.threshold or branch_pct < args.threshold:
            failed = True

    print(
        f"{'TOTAL (scope)':<62}{totals[0]:>6}{totals[1]:>6}{pct(totals[0], totals[1]):>8.1f}"
        f"{totals[2]:>5}{totals[3]:>6}{pct(totals[2], totals[3]):>8.1f}"
    )
    if failed:
        print(f"FAIL: scope is below {args.threshold:.0f}% statement or branch coverage")
        return 1
    print(f"PASS: scope meets {args.threshold:.0f}% statement and branch coverage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
