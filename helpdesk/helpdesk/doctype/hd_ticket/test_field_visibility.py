import frappe
from frappe.client import get as client_get
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import get_list_data
from helpdesk.field_visibility import fields_visible_to
from helpdesk.helpdesk.doctype.hd_ticket.api import get_one, get_ticket_customizations
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_fields_meta
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_template,
    make_ticket,
    set_default_template_visibility,
)

AGENT_EMAIL = "fv_agent@example.com"
CUSTOMER_EMAIL = "fv_customer@example.com"


class TestTicketFieldVisibility(IntegrationTestCase):
    """Default-template visible_to narrows what permission levels allow; it never widens."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.addCleanup(frappe.set_user, "Administrator")
        create_agent(AGENT_EMAIL)
        create_contact("FV Customer", CUSTOMER_EMAIL)

    def delete_as_administrator(self, doctype: str, name: str):
        # cleanups run before the set_user reset, whatever user the test ended as
        frappe.set_user("Administrator")
        frappe.delete_doc(doctype, name, force=True)

    def make_customer_ticket(self, **values):
        ticket = make_ticket(
            subject="Field visibility ticket",
            raised_by=CUSTOMER_EMAIL,
            **values,
        )
        self.addCleanup(self.delete_as_administrator, "HD Ticket", ticket.name)
        return ticket

    def show_to(self, fieldname: str, visible_to: str):
        self.addCleanup(set_default_template_visibility(fieldname, visible_to))

    def test_agents_only_field_is_stripped_for_customers(self):
        # response_by is at the customer-readable level; visible_to alone hides it
        self.show_to("response_by", "Agents")
        ticket = self.make_customer_ticket()

        frappe.set_user(CUSTOMER_EMAIL)
        self.assertFalse(client_get("HD Ticket", ticket.name).get("response_by"))
        frappe.set_user(AGENT_EMAIL)
        self.assertTrue(client_get("HD Ticket", ticket.name).get("response_by"))

    def test_customers_only_field_is_stripped_for_agents(self):
        self.show_to("priority", "Customers")
        ticket = self.make_customer_ticket()

        frappe.set_user(AGENT_EMAIL)
        self.assertFalse(client_get("HD Ticket", ticket.name).get("priority"))
        frappe.set_user(CUSTOMER_EMAIL)
        self.assertTrue(client_get("HD Ticket", ticket.name).get("priority"))

    def test_get_one_strips_hidden_fields(self):
        self.show_to("response_by", "Agents")
        ticket = self.make_customer_ticket()
        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name, is_customer_portal=True)
        self.assertFalse(result.get("response_by"))

    def test_get_list_data_drops_hidden_rows(self):
        self.show_to("response_by", "Agents")
        self.make_customer_ticket()
        frappe.set_user(CUSTOMER_EMAIL)
        result = get_list_data("HD Ticket", rows=["subject", "response_by"])
        self.assertNotIn("response_by", result["rows"])
        for row in result["data"]:
            self.assertNotIn("response_by", row)
            self.assertIn("subject", row)

    def test_agent_form_customizations_omit_customers_only_rows(self):
        self.show_to("priority", "Customers")
        frappe.set_user(AGENT_EMAIL)
        customizations = get_ticket_customizations()
        self.assertNotIn(
            "priority", [r.fieldname for r in customizations["custom_fields"]]
        )
        self.assertIn("priority", customizations["hidden_fields"])

    def test_non_default_template_choices_have_no_effect(self):
        self.show_to("priority", "Agents")
        template = make_template(
            "FV Other", [{"fieldname": "priority", "visible_to": "Everyone"}]
        )
        self.addCleanup(
            self.delete_as_administrator, "HD Ticket Template", template.name
        )

        frappe.set_user(CUSTOMER_EMAIL)
        fieldnames = [f.fieldname for f in get_fields_meta(template.name)]
        # the Default template rules, whatever this template claims
        self.assertNotIn("priority", fieldnames)
        frappe.set_user(AGENT_EMAIL)
        fieldnames = [f.fieldname for f in get_fields_meta(template.name)]
        self.assertIn("priority", fieldnames)

    def test_template_never_writes_permission_levels(self):
        before = frappe.get_meta("HD Ticket").get_field("priority").permlevel
        self.show_to("priority", "Agents")
        frappe.clear_cache(doctype="HD Ticket")
        self.assertEqual(
            frappe.get_meta("HD Ticket").get_field("priority").permlevel, before
        )

    def test_showing_an_internal_field_to_customers_is_refused(self):
        template = frappe.get_doc("HD Ticket Template", "Default")
        template.append(
            "fields", {"fieldname": "resolution_details", "visible_to": "Customers"}
        )
        with self.assertRaises(frappe.ValidationError):
            template.save(ignore_permissions=True)

    def test_hiding_informs_when_the_api_still_serves_the_field(self):
        frappe.clear_messages()
        self.show_to("priority", "Agents")
        # priority sits below the internal level, so the API keeps serving it
        self.assertTrue(any("still returns it" in str(m) for m in frappe.message_log))

    def test_template_save_refreshes_the_hidden_fields(self):
        self.assertNotIn("priority", fields_visible_to("Agents"))
        self.show_to("priority", "Agents")
        self.assertIn("priority", fields_visible_to("Agents"))

    def test_agent_workflow_columns_hidden_from_customers(self):
        """_user_tags and friends bypass permission levels and must never reach the portal."""
        ticket = self.make_customer_ticket()
        frappe.db.set_value(
            "HD Ticket",
            ticket.name,
            {"_user_tags": ",Internal Tag", "_assign": '["agent@test.com"]'},
        )

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name, is_customer_portal=True)
        self.assertFalse(result.get("_user_tags"))
        self.assertFalse(result.get("_assign"))
        self.assertFalse(result.get("tags"))

        frappe.set_user(AGENT_EMAIL)
        self.assertIn(
            "Internal Tag", client_get("HD Ticket", ticket.name).get("_user_tags")
        )
