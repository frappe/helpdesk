import frappe
from frappe.desk.doctype.tag.tag import add_tag, remove_tag
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_agent, make_ticket

AGENT_EMAIL = "helpdesk-tag-agent@example.com"


class TestTicketTags(FrappeTestCase):
    """The tag picker has no helpdesk endpoints: it relies on core Tag
    permissions (role "All") for list/create and on core add_tag/remove_tag
    for linking. These tests guard that contract."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_agent(AGENT_EMAIL)
        cls.ticket = make_ticket()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_agent_can_create_and_list_helpdesk_tags(self):
        frappe.set_user(AGENT_EMAIL)
        tag = frappe.get_doc(
            {"doctype": "Tag", "name": "tag-perm-test", "app": "helpdesk"}
        )
        tag.insert()
        names = frappe.get_list("Tag", filters={"app": "helpdesk"}, pluck="name")
        self.assertIn("tag-perm-test", names)

    def test_tag_round_trip_on_ticket(self):
        frappe.set_user(AGENT_EMAIL)
        add_tag("round-trip", "HD Ticket", self.ticket.name)

        user_tags = frappe.db.get_value("HD Ticket", self.ticket.name, "_user_tags")
        self.assertIn("round-trip", user_tags)
        self.assertTrue(
            frappe.db.exists(
                "Tag Link",
                {
                    "document_type": "HD Ticket",
                    "document_name": self.ticket.name,
                    "tag": "round-trip",
                },
            )
        )

        add_tag("round-trip", "HD Ticket", self.ticket.name)
        self.assertEqual(
            frappe.db.get_value("HD Ticket", self.ticket.name, "_user_tags").count(
                "round-trip"
            ),
            1,
        )

        remove_tag("round-trip", "HD Ticket", self.ticket.name)
        self.assertNotIn(
            "round-trip",
            frappe.db.get_value("HD Ticket", self.ticket.name, "_user_tags") or "",
        )
        self.assertFalse(
            frappe.db.exists(
                "Tag Link",
                {
                    "document_type": "HD Ticket",
                    "document_name": self.ticket.name,
                    "tag": "round-trip",
                },
            )
        )

    def test_app_field_exists_on_tag(self):
        self.assertTrue(
            frappe.db.exists("Custom Field", {"dt": "Tag", "fieldname": "app"})
        )
