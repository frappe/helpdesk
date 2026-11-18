"""BR1 (boundary / limit): tickets are auto-closed after N days of inactivity.

Source: close_tickets_after_n_days in
helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py

At unit level the database query is a test double, so these tests check what
the function decides and what it asks the database for: the switch, the cutoff
("now minus N days", strictly-older-than), the status it filters on, and what
happens per ticket. The N-1 / N / N+1 day behaviour against real stored
communications is covered again at the API and integration level.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from conftest import make_fake_frappe

import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket

NOW = datetime(2026, 11, 16, 12, 0, 0)


def run(enabled=1, status="Replied", days=7, due=(), save_error=None):
    """Run the job once against a fake database; return (fake frappe, docs)."""
    fake = make_fake_frappe()
    fake.db.get_single_value.return_value = enabled
    fake.db.get_value.return_value = (status, days)
    fake.db.sql.return_value = list(due)

    docs = {}

    def get_doc(doctype, name):
        doc = MagicMock(name=name)
        doc.name = name
        doc.status = status
        if save_error and name in save_error:
            doc.save.side_effect = save_error[name]
        docs[name] = doc
        return doc

    fake.get_doc.side_effect = get_doc
    with patch.object(hd_ticket, "frappe", fake), patch.object(
        hd_ticket, "now_datetime", return_value=NOW
    ):
        hd_ticket.close_tickets_after_n_days()
    return fake, docs


def test_job_does_nothing_when_auto_close_is_switched_off():
    fake, docs = run(enabled=0, due=["1"])
    fake.db.get_single_value.assert_called_once_with("HD Settings", "auto_close_tickets")
    fake.db.sql.assert_not_called()
    assert docs == {}


def test_settings_are_read_from_hd_settings():
    fake, _ = run()
    fake.db.get_value.assert_called_once_with(
        "HD Settings", "HD Settings", ["auto_close_status", "auto_close_after_days"]
    )


@pytest.mark.parametrize("days", [1, 6, 7, 8, 30], ids=lambda d: f"N={d}")
def test_cutoff_is_exactly_n_days_before_now(days):
    fake, _ = run(days=days)
    params = fake.db.sql.call_args.args[1]
    assert params["inactivity_cutoff"] == NOW - timedelta(days=days)


def test_query_selects_only_strictly_older_tickets_in_the_configured_status():
    fake, _ = run(status="Replied", days=7)
    query, params = fake.db.sql.call_args.args
    assert "t.status = %(status)s" in query
    assert "latest_comm.last_communication_date < %(inactivity_cutoff)s" in query
    assert "MAX(communication_date)" in query
    assert params["status"] == "Replied"
    assert fake.db.sql.call_args.kwargs == {"pluck": "name"}


def test_threshold_stored_as_text_is_treated_as_a_number():
    fake, _ = run(days="7")
    assert fake.db.sql.call_args.args[1]["inactivity_cutoff"] == NOW - timedelta(days=7)


def test_nothing_due_closes_nothing():
    fake, docs = run(due=[])
    assert docs == {}
    fake.db.commit.assert_not_called()


def test_no_rows_returned_as_none_is_handled():
    fake = make_fake_frappe()
    fake.db.get_single_value.return_value = 1
    fake.db.get_value.return_value = ("Replied", 7)
    fake.db.sql.return_value = None
    with patch.object(hd_ticket, "frappe", fake), patch.object(
        hd_ticket, "now_datetime", return_value=NOW
    ):
        hd_ticket.close_tickets_after_n_days()
    fake.get_doc.assert_not_called()


def test_each_due_ticket_is_closed_saved_commented_and_committed():
    fake, docs = run(days=7, due=["101", "102"])
    assert set(docs) == {"101", "102"}
    for doc in docs.values():
        assert doc.status == "Closed"
        assert doc.flags.ignore_validate is True
        doc.save.assert_called_once_with(ignore_permissions=True)
        doc.add_comment.assert_called_once_with(
            "Info", "automatically closed the ticket after 7 days of inactivity"
        )
    assert fake.db.commit.call_count == 2
    fake.log_error.assert_not_called()


def test_a_ticket_returned_twice_is_closed_once():
    fake, docs = run(due=["101", "101"])
    assert fake.get_doc.call_count == 1
    docs["101"].save.assert_called_once()


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (0, "automatically closed the ticket after 0 day of inactivity"),
        (1, "automatically closed the ticket after 1 day of inactivity"),
        (2, "automatically closed the ticket after 2 days of inactivity"),
    ],
    ids=["below-0", "at-1", "above-2"],
)
def test_comment_wording_at_the_singular_plural_boundary(days, expected):
    _, docs = run(days=days, due=["101"])
    docs["101"].add_comment.assert_called_once_with("Info", expected)


def test_a_ticket_that_fails_to_save_is_logged_and_the_rest_still_close():
    fake, docs = run(days=7, due=["101"], save_error={"101": RuntimeError("locked")})
    docs["101"].add_comment.assert_not_called()
    fake.db.commit.assert_not_called()
    fake.log_error.assert_called_once_with(
        message="Failed to auto close ticket 101 after 7 days. Error: locked",
        title="Auto Close Ticket Failed",
    )


def test_one_failure_does_not_stop_the_other_tickets():
    fake, docs = run(
        days=7, due=["101", "102"], save_error={"101": RuntimeError("locked")}
    )
    docs["102"].save.assert_called_once_with(ignore_permissions=True)
    docs["102"].add_comment.assert_called_once()
    assert fake.db.commit.call_count == 1
    assert fake.log_error.call_count == 1
