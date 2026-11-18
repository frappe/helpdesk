"""DEF-01 data repair (RCA-1, corrective action 2).

Before PR #38 the daily auto-close job saved tickets with
`flags.ignore_validate`, which skipped `before_save`, so a ticket it closed
got status Closed (category Resolved) but no `resolution_date`. The fix stops
new cases; this tool repairs the tickets already stored that way.

A ticket is repaired only when all of these hold:
  * its status category is Resolved,
  * its resolution date is empty,
  * it carries the job's own Info comment "automatically closed the ticket
    after N day(s) of inactivity".
Its resolution date is then set to the time of the earliest such comment,
which is when the job closed it. `modified` is left unchanged, and an Info
comment records the repair.

Resolved tickets with no date and no auto-close comment are listed but not
touched: the job did not close them, so the comment cannot date them.

Not repaired: the SLA figures the old job also skipped (`resolution_time`,
the last hold period). They depend on business hours at the original close
time; tickets with an SLA are flagged for review instead.

Usage (dry run by default), from apps/helpdesk:
    ../../env/bin/python tests/team/tools/repair_auto_close_dates.py --site helpdesk.localhost
    ... --execute       # write the dates
    ... --report FILE   # also save the result as JSON
"""

import argparse
import json

AUTO_CLOSE_PREFIX = "automatically closed the ticket after "
REPAIR_NOTE = "resolution date back-filled from the auto-close comment ({when}) (DEF-01 data repair)"


def find(frappe):
    """Return (to_repair, not_repairable): Resolved tickets with no resolution date."""
    rows = frappe.db.sql(
        """
        select t.name, t.status, t.sla,
               (select min(c.creation) from `tabComment` c
                 where c.reference_doctype = 'HD Ticket' and c.reference_name = t.name
                   and c.comment_type = 'Info' and c.content like %(prefix)s) as closed_at
        from `tabHD Ticket` t
        where t.status_category = 'Resolved' and t.resolution_date is null
        order by t.name
        """,
        {"prefix": AUTO_CLOSE_PREFIX + "%"},
        as_dict=True,
    )
    to_repair = [r for r in rows if r.closed_at]
    not_repairable = [r for r in rows if not r.closed_at]
    return to_repair, not_repairable


def repair(frappe, execute=False):
    """Find and (with execute=True) repair; return a summary dict."""
    to_repair, not_repairable = find(frappe)
    if execute:
        for row in to_repair:
            frappe.db.set_value("HD Ticket", row.name, "resolution_date", row.closed_at, update_modified=False)
            frappe.get_doc("HD Ticket", row.name).add_comment(
                "Info", REPAIR_NOTE.format(when=row.closed_at.strftime("%Y-%m-%d %H:%M:%S"))
            )
        frappe.db.commit()
    return {
        "executed": execute,
        "repaired" if execute else "would_repair": [
            {"ticket": r.name, "status": r.status, "resolution_date": str(r.closed_at), "sla": r.sla}
            for r in to_repair
        ],
        "sla_review": [r.name for r in to_repair if r.sla],
        "not_repairable": [{"ticket": r.name, "status": r.status} for r in not_repairable],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--site", default="helpdesk.localhost")
    parser.add_argument("--execute", action="store_true", help="write the dates (default: dry run)")
    parser.add_argument("--report", help="save the result as JSON")
    args = parser.parse_args()

    import os
    from pathlib import Path

    import frappe

    report = os.path.abspath(args.report) if args.report else None  # before changing directory
    os.chdir(Path(__file__).resolve().parents[5] / "sites")  # bench/apps/helpdesk/tests/team/tools
    frappe.init(args.site)
    frappe.connect()
    try:
        result = repair(frappe, execute=args.execute)
    finally:
        frappe.destroy()

    key = "repaired" if args.execute else "would_repair"
    print(f"{'Repaired' if args.execute else 'Dry run, would repair'}: {len(result[key])} ticket(s)")
    for row in result[key]:
        print(f"  {row['ticket']}  {row['status']}  resolution_date := {row['resolution_date']}  sla: {row['sla'] or '-'}")
    print(f"SLA figures to review (not changed): {len(result['sla_review'])}")
    print(f"Resolved without a date and without an auto-close comment (not touched): {len(result['not_repairable'])}")
    for row in result["not_repairable"]:
        print(f"  {row['ticket']}  {row['status']}")
    if report:
        with open(report, "w") as handle:
            json.dump(result, handle, indent=1)
        print(f"report: {report}")


if __name__ == "__main__":
    main()
