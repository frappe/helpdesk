import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.assignment_rule import get_assignment_rules_list
from helpdesk.test_utils import create_agent, create_contact


class TestAssignmentRulesList(IntegrationTestCase):
    """The Assignment Rules settings page lists rules through this endpoint."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        suffix = frappe.generate_hash(length=6)
        cls.manager = create_agent(f"rule-list-manager-{suffix}@example.com").name
        frappe.get_doc("User", cls.manager).add_roles("Agent Manager")
        cls.agent = create_agent(f"rule-list-agent-{suffix}@example.com").name
        cls.customer = create_contact(
            "Rule Customer", f"rule-list-{suffix}@example.com"
        )
        cls.staffed = make_rule(f"Staffed {suffix}", "HD Ticket", [cls.agent])
        cls.unstaffed = make_rule(f"Unstaffed {suffix}", "HD Ticket")
        cls.contact_rule = make_rule(f"Contact {suffix}", "Contact")

    def test_manager_lists_ticket_rules_newest_first(self) -> None:
        with self.set_user(self.manager):
            rules = get_assignment_rules_list()

        names = [rule.name for rule in rules]
        self.assertLess(names.index(self.unstaffed), names.index(self.staffed))
        self.assertEqual(
            rules[names.index(self.staffed)],
            {
                "name": self.staffed,
                "description": "Listed by the settings page",
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


def make_rule(name: str, document_type: str, users: list[str] | None = None) -> str:
    """A disabled rule, so it never enters the live assignment rule cache."""
    rule = frappe.get_doc(
        {
            "doctype": "Assignment Rule",
            "name": name,
            "assignment_rule_name": name,
            "document_type": document_type,
            "description": "Listed by the settings page",
            "assign_condition": "status == 'Open'",
            "rule": "Round Robin",
            "priority": 2,
            "disabled": 1,
            "assignment_days": [{"day": "Monday"}],
            "users": [{"user": user} for user in users or []],
        }
    ).insert(ignore_permissions=True)
    return rule.name
