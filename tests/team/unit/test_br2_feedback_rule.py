"""BR2 (critical module): a ticket cannot be resolved without feedback.

Source: HDTicket.validate_feedback in
helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py

    if (feedback_rating or status_category != "Resolved" or is_agent()
            or not has_agent_replied or not is_feedback_mandatory):
        return
    frappe.throw("Ticket must be resolved with a feedback")

Atomic conditions, written so that True always means "short-circuits to accept":

    A  feedback_rating is set
    B  status_category != "Resolved"
    C  the session user is an agent
    D  no agent has replied yet
    E  feedback is not mandatory in HD Settings

Decision  ACCEPT = A or B or C or D or E.   REJECT only when all five are False.

The MCC table is all 2^5 = 32 combinations. The MC/DC set is derived from it:
for each condition, the pair of rows that differ only in that condition and
flip the outcome. With an OR-chain every such pair shares the all-False row,
so MC/DC needs 6 rows (n + 1).
"""

import itertools
from unittest.mock import patch

import pytest
from conftest import DocStub, Thrown, borrow, make_fake_frappe

import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket


class Ticket(DocStub):
    pass


borrow(Ticket, HDTicket, "validate_feedback")

CONDITIONS = ("A", "B", "C", "D", "E")
MCC_TABLE = list(itertools.product([False, True], repeat=5))
ALL_FALSE = (False, False, False, False, False)


def run_validate_feedback(a, b, c, d, e):
    """Drive validate_feedback with one row of the truth table."""
    fake = make_fake_frappe()
    fake.get_cached_value.return_value = 0 if e else 1  # is_feedback_mandatory
    ticket = Ticket(
        feedback_rating=0.8 if a else 0,
        status_category="Open" if b else "Resolved",
        has_agent_replied=None if d else "COMM-0001",
    )
    with patch.object(hd_ticket, "frappe", fake), patch.object(
        hd_ticket, "is_agent", return_value=c
    ):
        ticket.validate_feedback()
    return fake


def row_id(row):
    return "".join("T" if value else "F" for value in row)


@pytest.mark.parametrize("row", MCC_TABLE, ids=row_id)
def test_mcc_every_condition_combination(row):
    """Multiple condition coverage: all 32 rows, each with its expected outcome."""
    expect_accept = any(row)
    if expect_accept:
        run_validate_feedback(*row)  # must not raise
    else:
        with pytest.raises(Thrown) as raised:
            run_validate_feedback(*row)
        assert raised.value.message == "Ticket must be resolved with a feedback"
        assert raised.value.exc is hd_ticket.frappe.ValidationError


def test_mcc_table_has_exactly_one_rejecting_row():
    assert len(MCC_TABLE) == 32
    assert [row for row in MCC_TABLE if not any(row)] == [ALL_FALSE]


def mcdc_pair(index):
    """The MCC row that differs from ALL_FALSE only in condition `index`."""
    row = list(ALL_FALSE)
    row[index] = True
    return tuple(row)


@pytest.mark.parametrize("index", range(5), ids=CONDITIONS)
def test_mcdc_each_condition_independently_decides_the_outcome(index):
    """MC/DC: toggling one condition alone flips reject -> accept."""
    with pytest.raises(Thrown):
        run_validate_feedback(*ALL_FALSE)

    run_validate_feedback(*mcdc_pair(index))  # same row, one condition flipped


def test_reads_the_mandatory_flag_from_hd_settings():
    fake = run_validate_feedback(False, False, False, False, True)
    fake.get_cached_value.assert_called_once_with(
        "HD Settings", "HD Settings", "is_feedback_mandatory"
    )
