import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import (
    assign_ticket,
    clear_ticket_assignments,
    disable_team_assignment_restriction,
    enable_team_assignment_restriction,
    get_ticket_assignees,
    make_agent,
    make_team,
    make_ticket,
)

TEAM_A = "Assignment Team A"
TEAM_B = "Assignment Team B"
CUSTOMER_EMAIL = "assign_customer@test.com"


class TestTeamAssignmentRestriction(IntegrationTestCase):
    """Covers `assign_within_team`, which blocks assigning a ticket to an agent
    outside the ticket's team."""

    def setUp(self):
        self.agent_a = make_agent("assign_a@test.com")
        self.agent_b = make_agent("assign_b@test.com")
        self.team_a = make_team(TEAM_A, members=[self.agent_a])
        make_team(TEAM_B, members=[self.agent_b])
        enable_team_assignment_restriction()
        self.addCleanup(disable_team_assignment_restriction)
        frappe.set_user(self.agent_a)

    def test_agent_outside_team_is_rejected(self):
        ticket = self.make_teamed_ticket()
        self.assertRaises(frappe.ValidationError, assign_ticket, ticket, self.agent_b)
        self.assertEqual(get_ticket_assignees(ticket), [])

    def test_agent_within_team_is_allowed(self):
        ticket = self.make_teamed_ticket()
        assign_ticket(ticket, self.agent_a)
        self.assertEqual(get_ticket_assignees(ticket), [self.agent_a])

    def test_bulk_assign_rejects_when_any_agent_is_outside_the_team(self):
        ticket = self.make_teamed_ticket()
        self.assertRaises(
            frappe.ValidationError, assign_ticket, ticket, self.agent_a, self.agent_b
        )

    def test_caller_supplied_assignment_rule_does_not_bypass(self):
        """`assign_to.add` copies the caller's `assignment_rule` onto the ToDo,
        so the exemption must key off a server-set flag, not that field."""
        rule = self.team_a.assignment_rule

        # the field really does reach the ToDo from the caller
        enable_team_assignment_restriction(within_team=0)
        unguarded = self.make_teamed_ticket()
        assign_ticket(unguarded, self.agent_b, assignment_rule=rule)
        self.assertEqual(
            frappe.db.get_value(
                "ToDo",
                {"reference_name": unguarded, "allocated_to": self.agent_b},
                "assignment_rule",
            ),
            rule,
        )

        # and carrying it must not buy an exemption
        enable_team_assignment_restriction()
        ticket = self.make_teamed_ticket()
        self.assertRaises(
            frappe.ValidationError,
            assign_ticket,
            ticket,
            self.agent_b,
            assignment_rule=rule,
        )
        self.assertEqual(get_ticket_assignees(ticket), [])

    def test_ticket_without_a_team_is_unrestricted(self):
        ticket = make_ticket(raised_by=CUSTOMER_EMAIL).name
        assign_ticket(ticket, self.agent_b)
        self.assertEqual(get_ticket_assignees(ticket), [self.agent_b])

    def test_setting_off_is_unrestricted(self):
        enable_team_assignment_restriction(within_team=0)
        ticket = self.make_teamed_ticket()
        assign_ticket(ticket, self.agent_b)
        self.assertEqual(get_ticket_assignees(ticket), [self.agent_b])

    def test_parent_setting_off_is_unrestricted(self):
        """The child setting keeps its stored value when team restrictions are
        switched off, so the parent alone must be enough to disable it."""
        enable_team_assignment_restriction(restrict_by_team=0)
        ticket = self.make_teamed_ticket()
        assign_ticket(ticket, self.agent_b)
        self.assertEqual(get_ticket_assignees(ticket), [self.agent_b])

    def test_administrator_bypasses_the_restriction(self):
        ticket = self.make_teamed_ticket()
        frappe.set_user("Administrator")
        assign_ticket(ticket, self.agent_b)
        self.assertEqual(get_ticket_assignees(ticket), [self.agent_b])

    def test_assignment_rule_is_exempt(self):
        """A team's own rule auto-assigns on insert; the guard must not break
        ticket creation."""
        ticket = make_ticket(agent_group=TEAM_A, raised_by=CUSTOMER_EMAIL).name
        self.assertEqual(get_ticket_assignees(ticket), [self.agent_a])

    def test_other_doctypes_are_untouched(self):
        todo = frappe.get_doc(
            {
                "doctype": "ToDo",
                "allocated_to": self.agent_b,
                "reference_type": "HD Team",
                "reference_name": TEAM_A,
                "description": "unrelated",
            }
        ).insert(ignore_permissions=True)
        self.assertEqual(todo.allocated_to, self.agent_b)

    def make_teamed_ticket(self) -> str:
        ticket = make_ticket(agent_group=TEAM_A, raised_by=CUSTOMER_EMAIL).name
        clear_ticket_assignments(ticket)
        return ticket

    def tearDown(self):
        frappe.set_user("Administrator")
