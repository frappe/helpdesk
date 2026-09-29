import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.assignment_rule import get_assignment_rules_list
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_agent_manager,
    make_assignment_rule,
    unique_email,
)


class TestAssignmentRulesList(IntegrationTestCase):
    """The Assignment Rules settings page lists rules through this endpoint."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        suffix = frappe.generate_hash(length=6)
        cls.manager = make_agent_manager("rule-list-manager")
        cls.agent = create_agent(unique_email("rule-list-agent")).name
        cls.customer = create_contact("Rule Customer", unique_email("rule-list"))
        cls.staffed = make_assignment_rule(
            f"Staffed {suffix}", "HD Ticket", [cls.agent]
        )
        cls.unstaffed = make_assignment_rule(f"Unstaffed {suffix}", "HD Ticket")
        cls.contact_rule = make_assignment_rule(f"Contact {suffix}", "Contact")

    def test_manager_lists_ticket_rules_newest_first(self) -> None:
        with self.set_user(self.manager):
            rules = get_assignment_rules_list()

        names = [rule.name for rule in rules]
        self.assertLess(names.index(self.unstaffed), names.index(self.staffed))
        self.assertEqual(
            rules[names.index(self.staffed)],
            {
                "name": self.staffed,
                "description": "Test assignment rule",
                "disabled": 1,
                "priority": 2,
                "users_exists": True,
            },
        )
        self.assertFalse(rules[names.index(self.unstaffed)]["users_exists"])

    def test_rules_for_other_doctypes_are_not_listed(self) -> None:
        with self.set_user(self.manager):
            names = [rule.name for rule in get_assignment_rules_list()]
        self.assertNotIn(self.contact_rule, names)

    def test_agent_cannot_list_rules(self) -> None:
        with self.set_user(self.agent):
            with self.assertRaises(frappe.PermissionError):
                get_assignment_rules_list()

    def test_customer_cannot_list_rules(self) -> None:
        with self.set_user(self.customer["user"]):
            with self.assertRaises(frappe.PermissionError):
                get_assignment_rules_list()
