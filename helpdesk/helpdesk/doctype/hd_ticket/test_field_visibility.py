import frappe
from frappe.client import get as client_get
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import get_list_data
from helpdesk.api.ticket_analytics import get_ticket_analytics
from helpdesk.field_visibility import TicketFieldVisibility, get_field_tiers
from helpdesk.helpdesk.doctype.hd_ticket.api import get_one, get_ticket_customizations
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_fields_meta
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_template,
    make_ticket,
    tier_default_template_field,
)

AGENT_EMAIL = "fv_agent@example.com"
MANAGER_EMAIL = "fv_manager@example.com"
CUSTOMER_EMAIL = "fv_customer@example.com"


class TestTicketFieldVisibility(IntegrationTestCase):
    """The Default template's visible_to tiers narrow, at helpdesk level,
    what permission levels allow — and never widen it. Templates do not
    write permission levels."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.addCleanup(frappe.set_user, "Administrator")
        create_agent(AGENT_EMAIL)
        create_agent(MANAGER_EMAIL)
        if "Agent Manager" not in frappe.get_roles(MANAGER_EMAIL):
            # reload: the HD Agent insert inside create_agent touches the User
            frappe.get_doc("User", MANAGER_EMAIL).add_roles("Agent Manager")
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

    def tier(self, fieldname: str, visible_to: str):
        self.addCleanup(tier_default_template_field(fieldname, visible_to))

    def test_agent_client_get_strips_manager_tier_fields(self):
        self.tier("total_hold_time", "Agent Managers and above")
        ticket = self.make_customer_ticket()
        frappe.db.set_value("HD Ticket", ticket.name, "total_hold_time", 3600)

        frappe.set_user(AGENT_EMAIL)
        self.assertFalse(client_get("HD Ticket", ticket.name).get("total_hold_time"))
        frappe.set_user(MANAGER_EMAIL)
        self.assertEqual(
            client_get("HD Ticket", ticket.name).get("total_hold_time"), 3600
        )

    def test_meta_narrows_below_the_permission_level(self):
        # response_by sits at the customer-visible level; the tier alone
        # takes it off the portal
        self.tier("response_by", "Agents and above")
        ticket = self.make_customer_ticket()
        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name, is_customer_portal=True)
        self.assertFalse(result.get("response_by"))
        # the UI drops hardcoded rows for hidden fields using this list
        self.assertIn("response_by", result["_hidden_fields"])

    def test_get_list_data_drops_tiered_rows(self):
        self.tier("response_by", "Agents and above")
        self.make_customer_ticket()
        frappe.set_user(CUSTOMER_EMAIL)
        result = get_list_data("HD Ticket", rows=["subject", "response_by"])
        self.assertNotIn("response_by", result["rows"])
        for row in result["data"]:
            self.assertNotIn("response_by", row)
            self.assertIn("subject", row)

    def test_analytics_omits_fields_above_agent_tier(self):
        self.tier("total_hold_time", "Agent Managers and above")
        ticket = self.make_customer_ticket()
        frappe.db.set_value("HD Ticket", ticket.name, "total_hold_time", 3600)

        frappe.set_user(AGENT_EMAIL)
        self.assertFalse(get_ticket_analytics(ticket.name)["metrics"]["hold_time"])
        frappe.set_user(MANAGER_EMAIL)
        self.assertEqual(
            get_ticket_analytics(ticket.name)["metrics"]["hold_time"], 3600
        )

    def test_agent_form_customizations_omit_above_tier_rows(self):
        self.tier("total_hold_time", "Agent Managers and above")
        frappe.set_user(AGENT_EMAIL)
        customizations = get_ticket_customizations()
        self.assertNotIn(
            "total_hold_time", [r.fieldname for r in customizations["custom_fields"]]
        )
        self.assertIn("total_hold_time", customizations["hidden_fields"])
        frappe.set_user(MANAGER_EMAIL)
        customizations = get_ticket_customizations()
        self.assertIn(
            "total_hold_time", [r.fieldname for r in customizations["custom_fields"]]
        )
        self.assertNotIn("total_hold_time", customizations["hidden_fields"])

    def test_non_default_template_tiers_have_no_effect(self):
        self.tier("priority", "Agent Managers and above")
        template = make_template(
            "FV Other", [{"fieldname": "priority", "visible_to": "Everyone"}]
        )
        self.addCleanup(
            self.delete_as_administrator, "HD Ticket Template", template.name
        )

        frappe.set_user(AGENT_EMAIL)
        fieldnames = [f.fieldname for f in get_fields_meta(template.name)]
        # the Default template rules, whatever this template claims
        self.assertNotIn("priority", fieldnames)
        frappe.set_user(MANAGER_EMAIL)
        fieldnames = [f.fieldname for f in get_fields_meta(template.name)]
        self.assertIn("priority", fieldnames)

    def test_template_never_writes_permission_levels(self):
        before = frappe.get_meta("HD Ticket").get_field("priority").permlevel
        self.tier("priority", "System Managers only")
        frappe.clear_cache(doctype="HD Ticket")
        self.assertEqual(
            frappe.get_meta("HD Ticket").get_field("priority").permlevel, before
        )

    def test_showing_an_internal_field_is_refused(self):
        template = frappe.get_doc("HD Ticket Template", "Default")
        template.append(
            "fields", {"fieldname": "resolution_details", "visible_to": "Everyone"}
        )
        with self.assertRaises(frappe.ValidationError):
            template.save(ignore_permissions=True)

    def test_showing_a_server_computed_field_is_refused(self):
        template = frappe.get_doc("HD Ticket Template", "Default")
        template.append(
            "fields", {"fieldname": "response_by", "visible_to": "Everyone"}
        )
        with self.assertRaises(frappe.ValidationError):
            template.save(ignore_permissions=True)

    def test_hiding_warns_when_the_api_still_serves_the_field(self):
        frappe.clear_messages()
        self.tier("priority", "Agents and above")
        # priority sits below the internal level, so the API keeps serving it
        self.assertTrue(any("still readable" in str(m) for m in frappe.message_log))

    def test_template_save_invalidates_field_tiers(self):
        self.tier("priority", "Agents and above")
        self.assertEqual(get_field_tiers().get("priority"), 1)

        # a row saved before the tier column existed falls back to the old flag
        row = frappe.db.get_value(
            "HD Ticket Template Field",
            {"parent": "Default", "fieldname": "priority"},
        )
        frappe.db.set_value(
            "HD Ticket Template Field", row, "visible_to", "", update_modified=False
        )
        get_field_tiers.clear_cache()
        self.assertEqual(get_field_tiers().get("priority"), 1)

    def test_agent_workflow_columns_hidden_from_customers(self):
        """_user_tags and friends are framework columns permission levels
        cannot cover; they carry agent workflow data and never reach the
        portal."""
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

    def test_customer_rank_is_zero_and_staff_ranks_climb(self):
        self.assertEqual(TicketFieldVisibility(CUSTOMER_EMAIL).rank, 0)
        self.assertEqual(TicketFieldVisibility(AGENT_EMAIL).rank, 1)
        self.assertEqual(TicketFieldVisibility(MANAGER_EMAIL).rank, 2)
