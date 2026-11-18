"""BR4 (state + role): what a customer may fill on insert and change afterwards.

Source: helpdesk/helpdesk/doctype/hd_ticket/customer_edit_controller.py
(whole file is in the 100% coverage scope).

Headline rule (check_update_perms): a non-agent cannot update a ticket that is
Closed or already rated.  Decision table for the two conditions:

    is_closed  is_rated  ->  outcome
    F          F             allowed
    F          T             PermissionError
    T          F             PermissionError
    T          T             PermissionError
"""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
import pytest
from conftest import DocStub, Thrown, borrow, field, make_fake_frappe

import helpdesk.helpdesk.doctype.hd_ticket.customer_edit_controller as cec
from helpdesk.consts import (
    CUSTOMER_ALWAYS_WRITABLE_FIELDS,
    PORTAL_INSERT_EXEMPT_FIELDS,
)
from helpdesk.helpdesk.doctype.hd_ticket.customer_edit_controller import (
    CustomerEditController,
)


class Ticket(DocStub):
    """DocStub plus the permission-level API the controller calls."""

    read_levels = (0, 7)
    write_levels = (0,)

    def get_permlevel_access(self, permission_type):
        return list(self.read_levels if permission_type == "read" else self.write_levels)


borrow(
    Ticket,
    CustomerEditController,
    "apply_ticket_insert_rules",
    "check_update_perms",
    "prevent_customer_edits",
    "customer_writable_after_create",
    "customer_writable_rows",
)


def row(fieldname, visible_to="Everyone", editable_after_creation=0):
    return frappe._dict(
        fieldname=fieldname,
        visible_to=visible_to,
        editable_after_creation=editable_after_creation,
    )


def meta(*fields):
    return SimpleNamespace(
        fields=list(fields),
        get_translated_label=lambda fieldname: fieldname.replace("_", " ").title(),
    )


class Env:
    """Patches the controller's collaborators for the duration of one test."""

    def __init__(self, agent=False, user="customer@example.com", roles=(), rows=(), unreadable=()):
        self.fake = make_fake_frappe(user=user, roles=roles)
        ticket_fields = SimpleNamespace(
            template_rows=list(rows), unreadable_fields=set(unreadable)
        )
        self._patches = [
            patch.object(cec, "frappe", self.fake),
            patch.object(cec, "is_agent", return_value=agent),
            patch.object(cec, "TicketFields", return_value=ticket_fields),
        ]

    def __enter__(self):
        for p in self._patches:
            p.start()
        return self

    def __exit__(self, *exc_info):
        for p in reversed(self._patches):
            p.stop()


# --- apply_ticket_insert_rules ---------------------------------------------


def test_insert_by_agent_is_left_alone():
    ticket = Ticket(new=True, raised_by="someone@else.com", via_customer_portal=0)
    with Env(agent=True):
        ticket.apply_ticket_insert_rules()
    assert ticket.raised_by == "someone@else.com"
    assert ticket.via_customer_portal == 0
    assert "ignore_permlevel_for_fields" not in ticket.flags


def test_insert_by_system_manager_is_left_alone():
    ticket = Ticket(new=True, raised_by="sender@mail.com", via_customer_portal=0)
    with Env(agent=False, roles=["System Manager"]):
        ticket.apply_ticket_insert_rules()
    assert ticket.raised_by == "sender@mail.com"
    assert ticket.via_customer_portal == 0


def test_insert_by_customer_is_stamped_with_the_session_user():
    ticket = Ticket(new=True, raised_by="spoofed@victim.com", meta=meta(field("subject")))
    with Env(user="customer@example.com", roles=["HD Customer"], rows=[row("subject")]):
        ticket.apply_ticket_insert_rules()
    assert ticket.raised_by == "customer@example.com"
    assert ticket.via_customer_portal == 1
    assert ticket.flags.ignore_permlevel_for_fields == [*PORTAL_INSERT_EXEMPT_FIELDS, "subject"]


def test_insert_by_guest_keeps_the_submitted_email():
    ticket = Ticket(new=True, raised_by="visitor@example.com", meta=meta())
    with Env(user="Guest", roles=["Guest"]):
        ticket.apply_ticket_insert_rules()
    assert ticket.raised_by == "visitor@example.com"
    assert ticket.via_customer_portal == 1
    assert ticket.flags.ignore_permlevel_for_fields == list(PORTAL_INSERT_EXEMPT_FIELDS)


# --- check_update_perms ------------------------------------------------------


def old(status="Open", feedback=None):
    return SimpleNamespace(status=status, feedback=feedback)


def test_update_check_is_skipped_for_a_new_ticket():
    with Env(agent=False):
        Ticket(new=True, before=None).check_update_perms()


def test_agent_may_update_a_closed_and_rated_ticket():
    with Env(agent=True):
        Ticket(before=old("Closed", "Great")).check_update_perms()


def test_rating_flag_bypasses_the_closed_ticket_guard():
    ticket = Ticket(before=old("Closed", None))
    ticket.flags.ignore_closed_ticket_guard = True
    with Env(agent=False):
        ticket.check_update_perms()


@pytest.mark.parametrize(
    ("status", "feedback", "allowed"),
    [
        ("Open", None, True),
        ("Open", "Great", False),
        ("Closed", None, False),
        ("Closed", "Great", False),
    ],
    ids=["FF-allowed", "FT-rated", "TF-closed", "TT-closed-and-rated"],
)
def test_decision_table_closed_or_rated(status, feedback, allowed):
    ticket = Ticket(before=old(status, feedback))
    with Env(agent=False):
        if allowed:
            ticket.check_update_perms()
            return
        with pytest.raises(Thrown) as raised:
            ticket.check_update_perms()
    assert raised.value.message == "Closed or rated tickets cannot be updated by non-agents"
    assert raised.value.exc is frappe.PermissionError


@pytest.mark.parametrize("status", ["Resolved", "Paused", "Replied"])
def test_only_the_closed_status_locks_an_unrated_ticket(status):
    with Env(agent=False):
        Ticket(before=old(status, None)).check_update_perms()


# --- customer_writable_rows --------------------------------------------------


def test_writable_rows_exclude_agent_only_unreadable_and_server_set_fields():
    ticket = Ticket(
        meta=meta(
            field("subject", permlevel=0),
            field("priority", permlevel=7),
            field("agent_group", permlevel=8),
            field("resolution_date", permlevel=7),
            field("ticket_type", permlevel=0),
        )
    )
    rows = [
        row("subject"),
        row("priority", visible_to="Customers"),
        row("agent_group"),  # permlevel 8: not readable by a customer
        row("resolution_date"),  # server computed
        row("ticket_type", visible_to="Agents"),  # agent-only in the template
    ]
    with Env(rows=rows):
        result = ticket.customer_writable_rows()
    assert [r.fieldname for r in result] == ["subject", "priority"]


# --- customer_writable_after_create -----------------------------------------


def writable(ticket, rows=()):
    ticket.meta = meta(*(field(r.fieldname) for r in rows))
    with Env(rows=rows):
        return ticket.customer_writable_after_create()


def test_always_writable_fields_plus_rows_marked_editable_after_creation():
    rows = [row("description", editable_after_creation=1), row("subject")]
    result = writable(Ticket(status="Open"), rows)
    assert result == {*CUSTOMER_ALWAYS_WRITABLE_FIELDS, "description"}


def test_status_is_writable_only_when_the_customer_closes():
    assert "status" in writable(Ticket(status="Closed"))
    assert "status" not in writable(Ticket(status="Resolved"))
    assert "status" not in writable(Ticket(status="Open"))


def test_status_is_writable_when_a_customer_reply_reopens_the_ticket():
    ticket = Ticket(status="Open")
    ticket.flags.customer_reply_reopen = True
    assert "status" in writable(ticket)


# --- prevent_customer_edits --------------------------------------------------


def edited_ticket(changed, fields, rows=(), **values):
    values.setdefault("status", "Open")
    return Ticket(changed=changed, meta=meta(*fields), **values), list(rows)


def test_edit_guard_is_skipped_for_a_new_ticket():
    with Env(agent=False):
        Ticket(new=True).prevent_customer_edits()


def test_edit_guard_is_skipped_for_an_agent():
    with Env(agent=True):
        Ticket(changed={"subject"}).prevent_customer_edits()


def test_edit_guard_is_skipped_when_the_server_sets_the_bypass_flag():
    ticket = Ticket(changed={"subject"})
    ticket.flags.ignore_customer_edit_guard = True
    with Env(agent=False):
        ticket.prevent_customer_edits()
    assert "ignore_permlevel_for_fields" not in ticket.flags


def test_customer_changing_nothing_is_accepted_and_editable_fields_are_exempted():
    ticket, rows = edited_ticket(set(), [field("subject")], subject="Printer")
    with Env(rows=rows):
        ticket.prevent_customer_edits()
    assert set(ticket.flags.ignore_permlevel_for_fields) == set(CUSTOMER_ALWAYS_WRITABLE_FIELDS)


def test_customer_changing_an_editable_field_is_accepted():
    rows = [row("description", editable_after_creation=1)]
    ticket, rows = edited_ticket(
        {"description", "feedback"},
        [field("description"), field("feedback")],
        rows,
        description="more detail",
        feedback="Great",
    )
    with Env(rows=rows):
        ticket.prevent_customer_edits()


def test_layout_fields_are_never_treated_as_changes():
    ticket, rows = edited_ticket({"section_1"}, [field("section_1", "Section Break")])
    with Env(rows=rows):
        ticket.prevent_customer_edits()


def test_unreadable_field_sent_back_blank_is_not_a_change():
    ticket, rows = edited_ticket({"key"}, [field("key", permlevel=8)], key=None)
    with Env(rows=rows, unreadable={"key"}):
        ticket.prevent_customer_edits()


def test_unreadable_field_sent_back_with_a_value_is_refused():
    ticket, rows = edited_ticket({"key"}, [field("key", permlevel=8)], key="forged")
    with Env(rows=rows, unreadable={"key"}):
        with pytest.raises(Thrown) as raised:
            ticket.prevent_customer_edits()
    assert raised.value.message == "You do not have permission to change Key"
    assert raised.value.exc is frappe.PermissionError


def test_changing_a_locked_field_at_a_writable_level_explains_it_is_locked():
    ticket, rows = edited_ticket(
        {"subject"}, [field("subject", permlevel=0)], subject="New subject"
    )
    with Env(rows=rows):
        with pytest.raises(Thrown) as raised:
            ticket.prevent_customer_edits()
    assert raised.value.message == "You cannot change Subject after the ticket is raised"
    assert raised.value.exc is frappe.PermissionError


def test_changing_an_agent_field_reports_missing_permission_for_that_field_only():
    ticket, rows = edited_ticket(
        {"subject", "priority", "agent_group"},
        [field("subject", permlevel=0), field("priority", permlevel=7), field("agent_group", permlevel=8)],
        subject="New subject",
        priority="Urgent",
        agent_group="Billing",
    )
    with Env(rows=rows):
        with pytest.raises(Thrown) as raised:
            ticket.prevent_customer_edits()
    assert raised.value.message == "You do not have permission to change Priority, Agent Group"


def test_customer_may_change_status_only_to_closed():
    closing, rows = edited_ticket({"status"}, [field("status")], status="Closed")
    with Env(rows=rows):
        closing.prevent_customer_edits()

    resolving, rows = edited_ticket({"status"}, [field("status")], status="Resolved")
    with Env(rows=rows):
        with pytest.raises(Thrown) as raised:
            resolving.prevent_customer_edits()
    assert raised.value.message == "You cannot change Status after the ticket is raised"
