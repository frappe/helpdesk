"""Supporting state rules: which ticket statuses may be renamed, edited or disabled.

Source: helpdesk/helpdesk/doctype/hd_ticket_status/hd_ticket_status.py
(whole file is in the 100% coverage scope). These rules protect the status
records that BR3 and BR1 depend on: the "Closed" status and the requirement
that every category keeps at least one usable status.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from conftest import DocStub, Thrown, borrow, make_fake_frappe

import helpdesk.helpdesk.doctype.hd_ticket_status.hd_ticket_status as hts
from helpdesk.helpdesk.doctype.hd_ticket_status.hd_ticket_status import HDTicketStatus


class Status(DocStub):
    pass


borrow(
    Status,
    HDTicketStatus,
    "before_rename",
    "validate",
    "validate_closed_status_change",
    "validate_required_categories",
    "validate_disabling_status",
)


def fake_db(count=1, sla_default=None, sla_reopen=None, settings_default="Open", settings_reopen="Open"):
    fake = make_fake_frappe()
    fake.db.count.return_value = count

    def exists(doctype, filters):
        return sla_default if "default_ticket_status" in filters else sla_reopen

    def single(doctype, fieldname):
        return settings_default if fieldname == "default_ticket_status" else settings_reopen

    fake.db.exists.side_effect = exists
    fake.db.get_single_value.side_effect = single
    return fake


def call(method_name, status, *args, **db):
    fake = fake_db(**db)
    with patch.object(hts, "frappe", fake):
        getattr(status, method_name)(*args)
    return fake


def before(name="Replied", category="Paused"):
    return SimpleNamespace(name=name, category=category)


# --- before_rename -----------------------------------------------------------


def test_closed_status_cannot_be_renamed():
    with pytest.raises(Thrown) as raised:
        call("before_rename", Status(), "Closed", "Done")
    assert raised.value.message == "The 'Closed' status cannot be renamed."


def test_other_statuses_can_be_renamed():
    call("before_rename", Status(), "Replied", "Answered")


# --- validate_closed_status_change ------------------------------------------


def test_new_status_skips_the_closed_check():
    call("validate_closed_status_change", Status(new=True, name="Closed"))


def test_missing_previous_version_skips_the_closed_check():
    call("validate_closed_status_change", Status(before=None, changed={"category"}))


@pytest.mark.parametrize("changed", [{"order"}, {"color"}, {"order", "color"}])
def test_closed_status_allows_color_and_order_changes(changed):
    status = Status(name="Closed", before=before("Closed", "Resolved"), changed=changed)
    call("validate_closed_status_change", status)


@pytest.mark.parametrize("changed", [set(), {"category"}, {"enabled"}])
def test_closed_status_rejects_any_other_change(changed):
    status = Status(name="Closed", before=before("Closed", "Resolved"), changed=changed)
    with pytest.raises(Thrown) as raised:
        call("validate_closed_status_change", status)
    assert raised.value.message == (
        "Only the 'color' and 'order' fields of the 'Closed' status can be modified."
    )


def test_non_closed_status_may_change_other_fields():
    status = Status(name="Replied", before=before("Replied"), changed={"category"})
    call("validate_closed_status_change", status)


# --- validate_required_categories -------------------------------------------


def test_new_status_skips_the_category_check():
    fake = call("validate_required_categories", Status(new=True, changed={"category"}))
    fake.db.count.assert_not_called()


def test_unchanged_category_skips_the_check():
    fake = call("validate_required_categories", Status(changed=set(), category="Paused"))
    fake.db.count.assert_not_called()


def test_missing_previous_version_skips_the_category_check():
    status = Status(changed={"category"}, category="Open", before=None)
    fake = call("validate_required_categories", status)
    fake.db.count.assert_not_called()


def test_previously_empty_category_skips_the_check():
    status = Status(changed={"category"}, category="Open", before=before(category=None))
    fake = call("validate_required_categories", status)
    fake.db.count.assert_not_called()


def test_same_category_value_is_not_counted():
    status = Status(changed={"category"}, category="Paused", before=before(category="Paused"))
    fake = call("validate_required_categories", status)
    fake.db.count.assert_not_called()


def test_moving_the_last_status_out_of_a_category_is_rejected():
    status = Status(name="Replied", changed={"category"}, category="Open", before=before())
    with pytest.raises(Thrown) as raised:
        call("validate_required_categories", status, count=0)
    assert raised.value.message == (
        "At least one ticket status with category 'Paused' must exist in the system."
    )


def test_moving_a_status_is_allowed_while_another_remains_in_the_category():
    status = Status(name="Replied", changed={"category"}, category="Open", before=before())
    fake = call("validate_required_categories", status, count=1)
    fake.db.count.assert_called_once_with(
        "HD Ticket Status", {"category": "Paused", "name": ["!=", "Replied"]}
    )


# --- validate_disabling_status ----------------------------------------------


def disabled(name="Replied", category="Paused"):
    return Status(name=name, category=category, enabled=0)


def test_new_status_skips_the_disable_check():
    fake = call("validate_disabling_status", Status(new=True, enabled=0))
    fake.db.count.assert_not_called()


def test_enabled_status_skips_the_disable_check():
    fake = call("validate_disabling_status", Status(enabled=1))
    fake.db.count.assert_not_called()


def test_disabling_is_allowed_when_another_status_covers_the_category():
    fake = call("validate_disabling_status", disabled(), count=1)
    fake.db.count.assert_called_once_with(
        "HD Ticket Status",
        {"enabled": 1, "name": ["not in", ["Replied", "Closed"]], "category": "Paused"},
    )


def test_disabling_the_last_enabled_status_of_a_category_is_rejected():
    with pytest.raises(Thrown) as raised:
        call("validate_disabling_status", disabled(), count=0)
    assert raised.value.message == (
        "At least one enabled status for <u>Paused</u> category must be enabled."
    )


@pytest.mark.parametrize(
    ("sla_default", "sla_reopen", "expected_lines"),
    [
        ("Standard", None, ["- Standard as Default Status<br>"]),
        (None, "Premium", ["- Premium as Reopen Status<br>"]),
        ("Standard", "Premium", ["- Standard as Default Status<br>", "- Premium as Reopen Status<br>"]),
    ],
    ids=["default-only", "reopen-only", "both"],
)
def test_status_used_by_an_sla_cannot_be_disabled(sla_default, sla_reopen, expected_lines):
    with pytest.raises(Thrown) as raised:
        call("validate_disabling_status", disabled(), sla_default=sla_default, sla_reopen=sla_reopen)
    message = raised.value.message
    assert message.startswith("Cannot disable this status as it is linked in the following SLAs:")
    assert message.endswith("Please update the SLA(s) to use a different status before disabling this status.")
    for line in expected_lines:
        assert line in message
    assert ("as Default Status" in message) is bool(sla_default)
    assert ("as Reopen Status" in message) is bool(sla_reopen)


@pytest.mark.parametrize(
    ("settings_default", "settings_reopen", "has_default", "has_reopen"),
    [
        ("Replied", "Open", True, False),
        ("Open", "Replied", False, True),
        ("Replied", "Replied", True, True),
    ],
    ids=["default-only", "reopen-only", "both"],
)
def test_status_used_by_hd_settings_cannot_be_disabled(settings_default, settings_reopen, has_default, has_reopen):
    with pytest.raises(Thrown) as raised:
        call(
            "validate_disabling_status",
            disabled(),
            settings_default=settings_default,
            settings_reopen=settings_reopen,
        )
    message = raised.value.message
    assert message.startswith("Cannot disable this status as it is linked in HD Settings:")
    assert message.endswith("Please update HD Settings to use a different status before disabling this status.")
    assert ("- Default Ticket Status<br>" in message) is has_default
    assert ("- Ticket Reopen Status<br>" in message) is has_reopen


def test_unused_status_can_be_disabled():
    fake = call("validate_disabling_status", disabled())
    fake.db.get_single_value.assert_any_call("HD Settings", "default_ticket_status")
    fake.db.get_single_value.assert_any_call("HD Settings", "ticket_reopen_status")


# --- validate ----------------------------------------------------------------


def test_validate_runs_all_three_checks():
    status = Status(name="Closed", before=before("Closed", "Resolved"), changed=set(), enabled=1)
    with pytest.raises(Thrown):
        call("validate", status)

    healthy = Status(name="Replied", before=before(), changed=set(), enabled=1, category="Paused")
    call("validate", healthy)
