"""Tests added after mutation analysis to kill surviving mutants.

The first Cosmic Ray run left 31 survivors (score 86.9%). 24 were killable and
fell into two weaknesses of the original test data; the S-numbers refer to
tests/team/mutation/SURVIVORS.md.

  * identity: `==` -> `is`. Test literals were the very same object as the
    literal in the source. Fixed by feeding equal-but-distinct strings
    (`fresh`), which is what the database really returns.
  * ordering: `!=` -> `>` / `==` -> `<=`. The chosen values happened to sort on
    the side that hides the fault. Fixed with a value on the other side.
"""

from unittest.mock import patch

import pytest
from conftest import Thrown, fresh, make_fake_frappe
from test_br1_auto_close import run as run_auto_close
from test_br3_resolution_date import NOW, previous, stamp
from test_br3_resolution_date import Ticket as TransitionTicket
from test_br4_customer_edit_controller import Env, field, meta, old, row
from test_br4_customer_edit_controller import Ticket as PortalTicket
from test_ticket_status_rules import Status, before, call, disabled

import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket

CUSTOM_STATUS = "Awaiting customer"  # sorts before "Closed"; statuses are user-defined


# --- customer_edit_controller.py ---------------------------------------------


def test_s1_customer_whose_email_sorts_before_guest_is_still_stamped():
    ticket = PortalTicket(new=True, raised_by="spoofed@victim.com", meta=meta())
    with Env(user="Alice@example.com", roles=["HD Customer"]):
        ticket.apply_ticket_insert_rules()
    assert ticket.raised_by == "Alice@example.com"


def test_s2_guest_read_from_the_session_is_recognised_by_value():
    ticket = PortalTicket(new=True, raised_by="visitor@example.com", meta=meta())
    with Env(user=fresh("Guest"), roles=["Guest"]):
        ticket.apply_ticket_insert_rules()
    assert ticket.raised_by == "visitor@example.com"


def test_s3_closed_status_read_from_the_database_locks_the_ticket():
    with Env(agent=False), pytest.raises(Thrown):
        PortalTicket(before=old(fresh("Closed"), None)).check_update_perms()


def test_s4_custom_status_sorting_before_closed_does_not_lock_the_ticket():
    with Env(agent=False):
        PortalTicket(before=old(CUSTOM_STATUS, None)).check_update_perms()


def writable(ticket, rows=()):
    ticket.meta = meta(*(field(r.fieldname) for r in rows))
    with Env(rows=rows):
        return ticket.customer_writable_after_create()


def test_s5_template_row_that_repeats_an_always_writable_field_stays_writable():
    result = writable(PortalTicket(status="Open"), [row("feedback", editable_after_creation=1)])
    assert "feedback" in result


def test_s6_closing_with_a_status_value_from_the_request_opens_status():
    assert "status" in writable(PortalTicket(status=fresh("Closed")))


def test_s7_custom_status_sorting_before_closed_does_not_open_status():
    assert "status" not in writable(PortalTicket(status=CUSTOM_STATUS))


def test_s8_row_with_blank_visibility_is_customer_writable():
    ticket = PortalTicket(meta=meta(field("subject")))
    with Env(rows=[row("subject", visible_to="")]):
        assert [r.fieldname for r in ticket.customer_writable_rows()] == ["subject"]


def test_s9_agent_only_row_read_from_the_database_is_excluded():
    ticket = PortalTicket(meta=meta(field("subject")))
    with Env(rows=[row("subject", visible_to=fresh("Agents"))]):
        assert ticket.customer_writable_rows() == []


# --- hd_ticket.py --------------------------------------------------------------


class FeedbackTicket(TransitionTicket):
    validate_feedback = HDTicket.__dict__["validate_feedback"]


def test_s10_resolved_category_read_from_the_database_still_requires_feedback():
    fake = make_fake_frappe()
    fake.get_cached_value.return_value = 1
    ticket = FeedbackTicket(
        feedback_rating=0, status_category=fresh("Resolved"), has_agent_replied="COMM-0001"
    )
    with patch.object(hd_ticket, "frappe", fake), patch.object(hd_ticket, "is_agent", return_value=False):
        with pytest.raises(Thrown):
            ticket.validate_feedback()


def test_s12_change_to_a_custom_status_sorting_before_closed_is_a_transition():
    ticket = TransitionTicket(changed={"status"}, status=CUSTOM_STATUS, before=previous("Resolved"))
    assert ticket.is_valid_status_transition() is True


def test_s13_closed_value_from_the_request_on_a_resolved_ticket_is_not_a_transition():
    ticket = TransitionTicket(changed={"status"}, status=fresh("Closed"), before=previous("Resolved"))
    assert ticket.is_valid_status_transition() is False


def test_s14_previous_resolved_category_from_the_database_is_recognised():
    ticket = TransitionTicket(changed={"status"}, status="Closed", before=previous(fresh("Resolved")))
    assert ticket.is_valid_status_transition() is False


def test_s16_entering_a_resolved_category_read_from_the_database_stamps_now():
    ticket = stamp(
        TransitionTicket(
            changed={"status", "status_category"},
            status="Resolved",
            status_category=fresh("Resolved"),
            before=previous("Open"),
            resolution_date=None,
        )
    )
    assert ticket.resolution_date == NOW


def test_s19_every_failing_ticket_is_logged_not_only_the_first():
    fake, docs = run_auto_close(
        days=7,
        due=["101", "102"],
        save_error={"101": RuntimeError("locked"), "102": RuntimeError("locked")},
    )
    assert fake.log_error.call_count == 2
    assert len(docs) == 2


# --- hd_ticket_status.py -------------------------------------------------------


def test_s21_closed_name_from_the_request_cannot_be_renamed():
    with pytest.raises(Thrown):
        call("before_rename", Status(), fresh("Closed"), "Done")


def test_s22_status_sorting_before_closed_can_be_renamed():
    call("before_rename", Status(), "Archived", "Old")


def test_s23_closed_record_loaded_from_the_database_rejects_other_changes():
    status = Status(name="Closed", before=before(fresh("Closed"), "Resolved"), changed={"category"})
    with pytest.raises(Thrown):
        call("validate_closed_status_change", status)


def test_s24_last_status_cannot_move_to_a_category_that_sorts_later():
    status = Status(name="Open", changed={"category"}, category="Paused", before=before("Open", "Open"))
    with pytest.raises(Thrown) as raised:
        call("validate_required_categories", status, count=0)
    assert "category 'Open'" in raised.value.message


def test_s25_equal_category_loaded_from_the_database_is_not_counted():
    status = Status(changed={"category"}, category="Paused", before=before(category=fresh("Paused")))
    fake = call("validate_required_categories", status)
    fake.db.count.assert_not_called()


def test_s28_s29_only_the_matching_settings_link_is_listed_default():
    with pytest.raises(Thrown) as raised:
        call(
            "validate_disabling_status",
            disabled(name=fresh("Replied")),
            settings_default="Replied",
            settings_reopen="Open",
        )
    assert "- Default Ticket Status<br>" in raised.value.message
    assert "- Ticket Reopen Status<br>" not in raised.value.message


def test_s29_default_link_is_not_listed_for_a_setting_that_sorts_later():
    with pytest.raises(Thrown) as raised:
        call("validate_disabling_status", disabled(), settings_default="Working", settings_reopen="Replied")
    assert "- Default Ticket Status<br>" not in raised.value.message
    assert "- Ticket Reopen Status<br>" in raised.value.message


def test_s30_reopen_link_is_listed_for_a_name_loaded_from_the_database():
    with pytest.raises(Thrown) as raised:
        call(
            "validate_disabling_status",
            disabled(name=fresh("Replied")),
            settings_default="Open",
            settings_reopen="Replied",
        )
    assert "- Ticket Reopen Status<br>" in raised.value.message


def test_s31_reopen_link_is_not_listed_for_a_setting_that_sorts_later():
    with pytest.raises(Thrown) as raised:
        call("validate_disabling_status", disabled(), settings_default="Replied", settings_reopen="Working")
    assert "- Default Ticket Status<br>" in raised.value.message
    assert "- Ticket Reopen Status<br>" not in raised.value.message
