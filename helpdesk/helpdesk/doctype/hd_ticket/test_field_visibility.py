import frappe
from frappe.client import get as client_get
from frappe.permissions import update_permission_property
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import get_filterable_fields, get_list_data
from helpdesk.consts import DEFAULT_TICKET_TEMPLATE, TICKET_INTERNAL_FIELD_PERMLEVEL
from helpdesk.helpdesk.doctype.hd_ticket.api import (
    get_one,
    get_ticket_customizations,
    merge_ticket,
)
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_fields_meta
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_one as get_ticket_form
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    create_customer,
    make_customer_ticket,
    make_template,
    raise_field_permlevel,
    reply_from_the_portal,
    set_default_template_visibility,
)

AGENT_EMAIL = "fv_agent@example.com"
CUSTOMER_EMAIL = "fv_customer@example.com"


class TestTicketFieldVisibility(IntegrationTestCase):
    """Default-template visible_to narrows what permission levels allow; it never widens."""

    def setUp(self):
        frappe.set_user("Administrator")
        create_agent(AGENT_EMAIL)
        self.contact = create_contact("FV Customer", CUSTOMER_EMAIL)["contact"]

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_agents_only_field_is_stripped_on_helpdesk_pages_not_framework_reads(self):
        """The tier is layout, not a permission; only the permlevel withholds a value."""
        self.addCleanup(set_default_template_visibility("response_by", "Agents"))
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)

        frappe.set_user(CUSTOMER_EMAIL)
        self.assertFalse(
            get_one(ticket.name, is_customer_portal=True).get("response_by")
        )
        self.assertTrue(client_get("HD Ticket", ticket.name).get("response_by"))
        frappe.set_user(AGENT_EMAIL)
        self.assertTrue(get_one(ticket.name).get("response_by"))

    def test_customers_only_field_is_stripped_for_agents(self):
        self.addCleanup(set_default_template_visibility("priority", "Customers"))
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)

        frappe.set_user(AGENT_EMAIL)
        self.assertFalse(get_one(ticket.name).get("priority"))
        frappe.set_user(CUSTOMER_EMAIL)
        self.assertTrue(get_one(ticket.name, is_customer_portal=True).get("priority"))

    def test_hiding_the_contact_fields_still_returns_a_ticket(self):
        """get_one used to build the contact card out of raised_by, which hiding removes."""
        self.addCleanup(set_default_template_visibility("contact", "Agents"))
        self.addCleanup(set_default_template_visibility("raised_by", "Agents"))
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name, is_customer_portal=True)
        self.assertEqual(result["contact"]["name"], "")
        self.assertFalse(result["contact"]["email_id"])

    def test_merge_records_the_link_without_write_at_the_internal_level(self):
        """The source closes either way; losing the link leaves no trace of where it went."""
        # a site whose Agent role never reached the internal level
        update_permission_property(
            "HD Ticket",
            "Agent",
            TICKET_INTERNAL_FIELD_PERMLEVEL,
            "write",
            0,
            validate=False,
        )
        self.addCleanup(frappe.clear_cache)
        self.addCleanup(frappe.db.delete, "Custom DocPerm", {"parent": "HD Ticket"})
        frappe.clear_cache()
        source = make_customer_ticket(self, CUSTOMER_EMAIL)
        target = make_customer_ticket(self, CUSTOMER_EMAIL)

        frappe.set_user(AGENT_EMAIL)
        merge_ticket(source=source.name, target=target.name)

        self.assertEqual(
            frappe.db.get_value("HD Ticket", source.name, "merged_with"), target.name
        )

    def test_a_portal_reply_reopens_a_ticket_the_agent_answered(self):
        """The edit guard must not treat the reopen as a customer edit."""
        for status in ("Replied", "Resolved"):
            with self.subTest(status=status):
                self.assertEqual(
                    reply_from_the_portal(self, CUSTOMER_EMAIL, status), "Open"
                )

    def test_a_portal_reply_cannot_reopen_a_closed_ticket(self):
        with self.assertRaises(frappe.PermissionError):
            reply_from_the_portal(self, CUSTOMER_EMAIL, "Closed")

    def test_permlevel_hidden_field_is_absent_from_list_columns_and_filters(self):
        """A column the query cannot return would be a header with no data under it."""
        make_customer_ticket(self, CUSTOMER_EMAIL, priority="High")
        raise_field_permlevel(self, "priority", TICKET_INTERNAL_FIELD_PERMLEVEL)

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_list_data(
            "HD Ticket",
            rows=["subject", "priority"],
            columns=[{"key": "subject"}, {"key": "priority"}],
        )
        self.assertNotIn("priority", [c.get("key") for c in result["columns"]])
        self.assertNotIn("priority", result["rows"])
        offered = [f.get("fieldname") for f in get_filterable_fields("HD Ticket")]
        self.assertNotIn("priority", offered)

    def test_agent_form_customizations_omit_customers_only_rows(self):
        self.addCleanup(set_default_template_visibility("priority", "Customers"))
        frappe.set_user(AGENT_EMAIL)
        shown = [f.fieldname for f in get_ticket_customizations()["fields"]]
        self.assertNotIn("priority", shown)
        # a core field needs no template row to be shown
        self.assertIn("agent_group", shown)

    def test_non_default_template_choices_have_no_effect(self):
        self.addCleanup(set_default_template_visibility("priority", "Agents"))
        template = make_template(
            "FV Other", [{"fieldname": "priority", "visible_to": "Everyone"}]
        )
        self.addCleanup(
            frappe.delete_doc, "HD Ticket Template", template.name, force=True
        )

        frappe.set_user(CUSTOMER_EMAIL)
        fieldnames = [f.fieldname for f in get_fields_meta(template.name)]
        # the Default template rules, whatever this template claims
        self.assertNotIn("priority", fieldnames)
        frappe.set_user(AGENT_EMAIL)
        fieldnames = [f.fieldname for f in get_fields_meta(template.name)]
        self.assertIn("priority", fieldnames)

    def test_showing_an_internal_field_to_customers_is_refused(self):
        template = frappe.get_doc("HD Ticket Template", "Default")
        template.append(
            "fields", {"fieldname": "resolution_details", "visible_to": "Customers"}
        )
        with self.assertRaises(frappe.ValidationError):
            template.save(ignore_permissions=True)

    def test_hiding_warns_once_and_only_for_fields_the_api_still_serves(self):
        """The warning names the rows this save hides, not every hidden row, forever."""
        frappe.clear_messages()
        self.addCleanup(set_default_template_visibility("priority", "Agents"))
        self.assertTrue(any("Priority" in str(m) for m in frappe.message_log))

        # a save that hides nothing new is not nagged about
        frappe.clear_messages()
        frappe.get_doc("HD Ticket Template", "Default").save(ignore_permissions=True)
        self.assertFalse(frappe.message_log)

        # an internal-level field is already hidden everywhere
        self.addCleanup(set_default_template_visibility("resolution_details", "Agents"))
        self.assertFalse(frappe.message_log)

    def test_subject_cannot_be_added_to_a_template(self):
        """Every form draws the title on its own; a row for it only fights them."""
        template = frappe.get_doc("HD Ticket Template", DEFAULT_TICKET_TEMPLATE)
        template.append("fields", {"fieldname": "subject"})
        with self.assertRaises(frappe.ValidationError):
            template.save()

    def test_the_default_template_cannot_be_renamed(self):
        """Renaming it would leave every visible_to lookup finding nothing."""
        with self.assertRaises(frappe.PermissionError):
            frappe.rename_doc("HD Ticket Template", "Default", "Renamed Default")

    def test_agent_workflow_columns_hidden_from_customers(self):
        """_user_tags and friends bypass permission levels and must never reach the portal."""
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)
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

    def test_agents_only_row_is_absent_from_the_customer_form_payloads(self):
        """The portal draws every row it is handed, so the label would leak
        even once the value is stripped off the ticket."""
        self.addCleanup(set_default_template_visibility("priority", "Everyone"))
        self.addCleanup(set_default_template_visibility("response_by", "Agents"))
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)

        frappe.set_user(CUSTOMER_EMAIL)
        rows = get_one(ticket.name, is_customer_portal=True)["template"]["fields"]
        self.assertEqual(["priority"], [row["fieldname"] for row in rows])
        # nothing ships the tier to the client, so no page can re-filter on it
        self.assertNotIn("visible_to", rows[0])
        fields = get_ticket_form(DEFAULT_TICKET_TEMPLATE)["fields"]
        self.assertEqual(["priority"], [field.fieldname for field in fields])

        frappe.set_user(AGENT_EMAIL)
        rows = get_one(ticket.name)["template"]["fields"]
        self.assertIn("response_by", [row["fieldname"] for row in rows])
        fields = get_ticket_form(DEFAULT_TICKET_TEMPLATE)["fields"]
        self.assertIn("response_by", [field.fieldname for field in fields])

    def test_a_multi_customer_contact_still_gets_a_required_customer_field(self):
        """set_customer_field only narrows a row get_fields_meta already allowed."""
        self.addCleanup(set_default_template_visibility("customer", "Everyone"))
        for name in ("FV Customer One", "FV Customer Two"):
            customer = create_customer(name, [{"contact_name": self.contact}])
            self.addCleanup(frappe.delete_doc, "HD Customer", customer.name, force=True)
        setting = "auto_set_customer_from_contact"
        original = frappe.db.get_single_value("HD Settings", setting)
        frappe.db.set_single_value("HD Settings", setting, 1)  # nosemgrep
        self.addCleanup(frappe.db.set_single_value, "HD Settings", setting, original)

        frappe.set_user(CUSTOMER_EMAIL)
        fields = get_ticket_form(DEFAULT_TICKET_TEMPLATE)["fields"]
        customer_field = next(f for f in fields if f.fieldname == "customer")
        self.assertTrue(customer_field.required)
