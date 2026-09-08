import frappe
from frappe.desk.form.assign_to import add as assign
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import make_agent, make_team, make_ticket

TEAM_A = "Assignment Team A"
TEAM_B = "Assignment Team B"
CUSTOMER_EMAIL = "assign_customer@test.com"


class TestTeamAssignmentRestriction(IntegrationTestCase):
    """Covers `assign_within_team`, which blocks assigning a ticket to an agent
    outside the ticket's team."""

    def setUp(self):
        self.agent_a = make_agent("assign_a@test.com")
        self.agent_b = make_agent("assign_b@test.com")
        make_team(TEAM_A, members=[self.agent_a])
        make_team(TEAM_B, members=[self.agent_b])
        self.set_settings(restrict_tickets_by_agent_group=1, assign_within_team=1)
        frappe.set_user(self.agent_a)

    def test_agent_outside_team_is_rejected(self):
        ticket = self.make_teamed_ticket()
        self.assertRaises(frappe.ValidationError, self.assign_to, ticket, self.agent_b)
        self.assertEqual(self.assignees(ticket), [])

    def test_agent_within_team_is_allowed(self):
        ticket = self.make_teamed_ticket()
        self.assign_to(ticket, self.agent_a)
        self.assertEqual(self.assignees(ticket), [self.agent_a])

    def test_bulk_assign_rejects_when_any_agent_is_outside_the_team(self):
        ticket = self.make_teamed_ticket()
        self.assertRaises(
            frappe.ValidationError, self.assign_to, ticket, self.agent_a, self.agent_b
        )

    def test_ticket_without_a_team_is_unrestricted(self):
        ticket = make_ticket(raised_by=CUSTOMER_EMAIL)
        self.assign_to(ticket, self.agent_b)
        self.assertEqual(self.assignees(ticket), [self.agent_b])

    def test_setting_off_is_unrestricted(self):
        self.set_settings(assign_within_team=0)
        ticket = self.make_teamed_ticket()
        self.assign_to(ticket, self.agent_b)
        self.assertEqual(self.assignees(ticket), [self.agent_b])

    def test_parent_setting_off_is_unrestricted(self):
        """The child setting keeps its stored value when team restrictions are
        switched off, so the parent alone must be enough to disable it."""
        self.set_settings(restrict_tickets_by_agent_group=0)
        ticket = self.make_teamed_ticket()
        self.assign_to(ticket, self.agent_b)
        self.assertEqual(self.assignees(ticket), [self.agent_b])

    def test_administrator_bypasses_the_restriction(self):
        ticket = self.make_teamed_ticket()
        frappe.set_user("Administrator")
        self.assign_to(ticket, self.agent_b)
        self.assertEqual(self.assignees(ticket), [self.agent_b])

    def test_assignment_rule_is_exempt(self):
        """A team's own rule auto-assigns on insert; the guard must not break
        ticket creation."""
        ticket = make_ticket(agent_group=TEAM_A, raised_by=CUSTOMER_EMAIL)
        self.assertEqual(self.assignees(ticket), [self.agent_a])

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

    def make_teamed_ticket(self):
        ticket = make_ticket(agent_group=TEAM_A, raised_by=CUSTOMER_EMAIL)
        # The team's own assignment rule auto-assigns on insert; start clean.
        frappe.db.delete(
            "ToDo", {"reference_type": "HD Ticket", "reference_name": ticket.name}
        )
        return ticket

    def assign_to(self, ticket, *users: str):
        assign({"doctype": "HD Ticket", "name": ticket.name, "assign_to": list(users)})

    def assignees(self, ticket) -> list[str]:
        return frappe.get_all(
            "ToDo",
            filters={
                "reference_type": "HD Ticket",
                "reference_name": ticket.name,
                "status": "Open",
            },
            pluck="allocated_to",
        )

    def set_settings(self, **values):
        for field, value in values.items():
            frappe.db.set_single_value("HD Settings", field, value)
            self.addCleanup(frappe.db.set_single_value, "HD Settings", field, 0)

    def tearDown(self):
        frappe.set_user("Administrator")
