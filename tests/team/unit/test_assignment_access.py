"""DEF-02 / DEF-03 fix: who may assign a ticket, and to whom.

Source: HDTicket.assign_agent in helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py

    @frappe.whitelist()
    @agent_only                      # caller must be an agent       (DEF-02)
    def assign_agent(self, agent):
        if not is_agent(agent):      # target must be an agent       (DEF-03)
            frappe.throw("Tickets can only be assigned to agents", ValidationError)
        assign({...})

Decision table (two conditions, all four combinations):

    caller is agent | target is agent | outcome
    ----------------+-----------------+------------------------------------------
    no              | no              | PermissionError, nothing assigned
    no              | yes             | PermissionError, nothing assigned (DEF-02)
    yes             | no              | ValidationError, nothing assigned (DEF-03)
    yes             | yes             | assigned to the target
"""

from unittest.mock import patch

import pytest
from conftest import DocStub, Thrown, make_fake_frappe

import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket
import helpdesk.utils as helpdesk_utils
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket

CALLER = "caller@example.com"
TARGET = "target@example.com"


class Ticket(DocStub):
    pass


# the real method as the class holds it: whitelisted and wrapped by agent_only
Ticket.assign_agent = HDTicket.__dict__["assign_agent"]


def run_assign(caller_is_agent, target_is_agent):
    """Call assign_agent with the two conditions set.

    Returns (assign double, Thrown or None)."""
    fake = make_fake_frappe(user=CALLER)
    agents = {CALLER} if caller_is_agent else set()
    if target_is_agent:
        agents.add(TARGET)

    def is_agent(user=None):
        return (user or CALLER) in agents

    ticket = Ticket(name="0042")
    error = None
    with patch.object(hd_ticket, "frappe", fake), patch.object(helpdesk_utils, "frappe", fake), \
            patch.object(hd_ticket, "is_agent", side_effect=is_agent), \
            patch.object(helpdesk_utils, "is_agent", side_effect=is_agent), \
            patch.object(hd_ticket, "_", side_effect=str), \
            patch.object(helpdesk_utils, "_", side_effect=str), \
            patch.object(hd_ticket, "assign") as assign:
        try:
            ticket.assign_agent(TARGET)
        except Thrown as thrown:
            error = thrown
    return assign, error


DECISION_TABLE = [
    # caller agent, target agent, expected exception, assigned
    (False, False, "PermissionError", False),
    (False, True, "PermissionError", False),
    (True, False, "ValidationError", False),
    (True, True, None, True),
]


@pytest.mark.parametrize(
    ("caller_is_agent", "target_is_agent", "expected_exc", "assigned"),
    DECISION_TABLE,
    ids=["caller-no/target-no", "caller-no/target-yes", "caller-yes/target-no", "caller-yes/target-yes"],
)
def test_decision_table(caller_is_agent, target_is_agent, expected_exc, assigned):
    assign, error = run_assign(caller_is_agent, target_is_agent)
    if expected_exc:
        assert error is not None
        assert error.exc is getattr(hd_ticket.frappe, expected_exc)
    else:
        assert error is None
    assert assign.called is assigned


def test_the_refusal_to_assign_a_non_agent_says_why():
    _, error = run_assign(caller_is_agent=True, target_is_agent=False)
    assert error.message == "Tickets can only be assigned to agents"


def test_the_ticket_is_assigned_to_the_requested_agent():
    assign, _ = run_assign(caller_is_agent=True, target_is_agent=True)
    assign.assert_called_once_with({"assign_to": [TARGET], "doctype": "HD Ticket", "name": "0042"})


def test_the_target_is_checked_by_its_own_user_not_the_caller():
    """Mutation guard: is_agent(agent) must look at the target, not the session user."""
    _, error = run_assign(caller_is_agent=True, target_is_agent=False)
    assert error is not None  # is_agent() with no argument would have accepted the caller
