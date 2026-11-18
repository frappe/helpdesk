"""DEF-01 data repair: tickets the auto-close job closed before PR #38.

The pre-fix job is reproduced exactly as it was (`flags.ignore_validate`, then
the Info comment), so the stored data looks like what the defect left behind.
The repair tool (tools/repair_auto_close_dates.py) must date those tickets
from the comment, leave everything else alone, and be safe to run twice.
"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import repair_auto_close_dates as tool  # noqa: E402

N = 7


def close_as_before_the_fix(site, name, comment=True):
    """What close_tickets_after_n_days did on the baseline (e326986)."""
    frappe = site.frappe
    site.fresh()
    doc = frappe.get_doc("HD Ticket", name)
    doc.status = "Closed"
    doc.flags.ignore_validate = True
    doc.save(ignore_permissions=True)
    if comment:
        doc.add_comment("Info", f"automatically closed the ticket after {N} days of inactivity")
    frappe.db.commit()


def stored(site, name, *fields):
    site.fresh()
    return site.frappe.db.get_value("HD Ticket", name, list(fields), as_dict=True)


def comment_time(site, name):
    site.fresh()
    return site.frappe.db.get_value(
        "Comment",
        {"reference_doctype": "HD Ticket", "reference_name": name, "content": ["like", tool.AUTO_CLOSE_PREFIX + "%"]},
        "creation",
    )


@pytest.fixture
def broken_ticket(customer_a, agent, site):
    """A ticket closed by the pre-fix job: Resolved category, no resolution date."""
    name = customer_a.new_ticket(subject="Data repair: auto-closed before the fix")
    assert agent.update_ticket(name, {"status": "Replied"}).status_code == 200
    close_as_before_the_fix(site, name)
    row = stored(site, name, "status", "status_category", "resolution_date")
    assert (row.status, row.status_category, row.resolution_date) == ("Closed", "Resolved", None)  # DEF-01 data
    return name


def test_dry_run_lists_the_ticket_and_changes_nothing(site, broken_ticket):
    before = stored(site, broken_ticket, "resolution_date", "modified")

    result = tool.repair(site.frappe, execute=False)

    assert broken_ticket in [r["ticket"] for r in result["would_repair"]]
    assert stored(site, broken_ticket, "resolution_date", "modified") == before


def test_execute_dates_the_ticket_from_the_auto_close_comment(site, broken_ticket):
    closed_at = comment_time(site, broken_ticket)
    modified = stored(site, broken_ticket, "modified").modified
    time.sleep(1)  # so an accidental update of `modified` would show

    result = tool.repair(site.frappe, execute=True)

    assert broken_ticket in [r["ticket"] for r in result["repaired"]]
    after = stored(site, broken_ticket, "resolution_date", "modified", "status")
    assert after.resolution_date == closed_at
    assert after.modified == modified
    assert after.status == "Closed"
    notes = site.frappe.get_all(
        "Comment",
        filters={"reference_doctype": "HD Ticket", "reference_name": broken_ticket, "content": ["like", "%DEF-01 data repair%"]},
        pluck="content",
    )
    assert len(notes) == 1


def test_running_the_repair_again_changes_nothing(site, broken_ticket):
    tool.repair(site.frappe, execute=True)
    first = stored(site, broken_ticket, "resolution_date", "modified")

    result = tool.repair(site.frappe, execute=True)

    assert broken_ticket not in [r["ticket"] for r in result["repaired"]]
    assert stored(site, broken_ticket, "resolution_date", "modified") == first
    notes = site.frappe.db.count(
        "Comment", {"reference_doctype": "HD Ticket", "reference_name": broken_ticket, "content": ["like", "%DEF-01 data repair%"]}
    )
    assert notes == 1


def test_a_resolved_ticket_without_the_jobs_comment_is_not_touched(customer_a, agent, site):
    name = customer_a.new_ticket(subject="Data repair: closed without the job's comment")
    assert agent.update_ticket(name, {"status": "Replied"}).status_code == 200
    close_as_before_the_fix(site, name, comment=False)

    result = tool.repair(site.frappe, execute=True)

    assert name in [r["ticket"] for r in result["not_repairable"]]
    assert stored(site, name, "resolution_date").resolution_date is None


def test_tickets_the_fixed_job_closes_need_no_repair(customer_a, agent, site):
    """After PR #38 the job stamps the date itself, so nothing is left to repair."""
    name = customer_a.new_ticket(subject="Data repair: closed by the fixed job")
    assert agent.update_ticket(name, {"status": "Replied"}).status_code == 200
    site.age_conversation(name, N + 1)
    site.run_auto_close()

    result = tool.repair(site.frappe, execute=False)

    assert stored(site, name, "resolution_date").resolution_date is not None
    assert name not in [r["ticket"] for r in result["would_repair"]]
    assert name not in [r["ticket"] for r in result["not_repairable"]]
