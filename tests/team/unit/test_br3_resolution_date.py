"""BR3 (change of state): when the resolution date is stamped, kept or cleared.

Source: HDTicket.is_valid_status_transition and HDTicket.set_resolution_date in
helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py

Rule, as read from the source:
  * A save that does not change `status` (or a brand-new ticket) is not a
    transition, so the resolution fields are left alone.
  * Moving to any status outside the Resolved category clears the date and time.
  * Moving into the Resolved category stamps "now".
  * Closing a ticket that was already Resolved is not a new outcome: the
    original resolution date is kept.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from conftest import DocStub, borrow

import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket

NOW = datetime(2026, 11, 16, 10, 30, 0)
EARLIER = datetime(2026, 11, 10, 9, 0, 0)


class Ticket(DocStub):
    pass


borrow(Ticket, HDTicket, "is_valid_status_transition", "set_resolution_date")


def previous(status_category):
    return SimpleNamespace(status_category=status_category)


# --- is_valid_status_transition -------------------------------------------


def test_new_ticket_is_not_a_transition():
    ticket = Ticket(new=True, changed={"status"}, status="Open")
    assert ticket.is_valid_status_transition() is False


def test_unchanged_status_is_not_a_transition():
    ticket = Ticket(changed=set(), status="Replied")
    assert ticket.is_valid_status_transition() is False


@pytest.mark.parametrize("status", ["Open", "Replied", "Paused", "Resolved"])
def test_change_to_any_status_other_than_closed_is_a_transition(status):
    ticket = Ticket(changed={"status"}, status=status, before=previous("Resolved"))
    assert ticket.is_valid_status_transition() is True


@pytest.mark.parametrize("old_category", ["Open", "Paused"])
def test_closing_an_unresolved_ticket_is_a_transition(old_category):
    ticket = Ticket(changed={"status"}, status="Closed", before=previous(old_category))
    assert ticket.is_valid_status_transition() is True


def test_closing_an_already_resolved_ticket_is_not_a_transition():
    ticket = Ticket(changed={"status"}, status="Closed", before=previous("Resolved"))
    assert ticket.is_valid_status_transition() is False


def test_closing_without_a_previous_version_is_a_transition():
    ticket = Ticket(changed={"status"}, status="Closed", before=None)
    assert ticket.is_valid_status_transition() is True


# --- set_resolution_date ---------------------------------------------------


def stamp(ticket):
    with patch.object(hd_ticket, "now_datetime", return_value=NOW):
        ticket.set_resolution_date()
    return ticket


def test_no_transition_leaves_resolution_fields_untouched():
    ticket = stamp(
        Ticket(
            changed=set(),
            status="Resolved",
            status_category="Resolved",
            resolution_date=EARLIER,
            resolution_time=120,
        )
    )
    assert ticket.resolution_date == EARLIER
    assert ticket.resolution_time == 120


@pytest.mark.parametrize("category", ["Open", "Paused"])
def test_leaving_resolved_clears_date_and_time(category):
    ticket = stamp(
        Ticket(
            changed={"status", "status_category"},
            status="Replied",
            status_category=category,
            before=previous("Resolved"),
            resolution_date=EARLIER,
            resolution_time=120,
        )
    )
    assert ticket.resolution_date is None
    assert ticket.resolution_time is None


def test_entering_resolved_stamps_now():
    ticket = stamp(
        Ticket(
            changed={"status", "status_category"},
            status="Resolved",
            status_category="Resolved",
            before=previous("Open"),
            resolution_date=None,
            resolution_time=None,
        )
    )
    assert ticket.resolution_date == NOW


def test_reresolving_after_reopen_restamps_even_if_a_date_is_present():
    ticket = stamp(
        Ticket(
            changed={"status", "status_category"},
            status="Resolved",
            status_category="Resolved",
            before=previous("Open"),
            resolution_date=EARLIER,
        )
    )
    assert ticket.resolution_date == NOW


def test_switching_between_two_resolved_statuses_keeps_the_original_date():
    """status changes, category stays Resolved, date already set -> keep it."""
    ticket = stamp(
        Ticket(
            changed={"status"},
            status="Resolved - Won't fix",
            status_category="Resolved",
            before=previous("Resolved"),
            resolution_date=EARLIER,
        )
    )
    assert ticket.resolution_date == EARLIER


def test_resolved_status_without_a_date_is_stamped_even_if_category_unchanged():
    ticket = stamp(
        Ticket(
            changed={"status"},
            status="Resolved - Won't fix",
            status_category="Resolved",
            before=previous("Resolved"),
            resolution_date=None,
        )
    )
    assert ticket.resolution_date == NOW


def test_closing_an_open_ticket_stamps_now():
    """Closed belongs to the Resolved category, so closing directly resolves."""
    ticket = stamp(
        Ticket(
            changed={"status", "status_category"},
            status="Closed",
            status_category="Resolved",
            before=previous("Open"),
            resolution_date=None,
        )
    )
    assert ticket.resolution_date == NOW


def test_closing_a_resolved_ticket_keeps_the_original_resolution_date():
    ticket = stamp(
        Ticket(
            changed={"status"},
            status="Closed",
            status_category="Resolved",
            before=previous("Resolved"),
            resolution_date=EARLIER,
        )
    )
    assert ticket.resolution_date == EARLIER
