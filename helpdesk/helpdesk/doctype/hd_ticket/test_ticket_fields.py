import frappe
from frappe.client import get as client_get
from frappe.permissions import update_permission_property
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import get_visible_custom_fields
from helpdesk.consts import (
    CORE_TICKET_FIELDS,
    DEFAULT_TICKET_TEMPLATE,
    TICKET_INTERNAL_FIELD_PERMLEVEL,
)
from helpdesk.helpdesk.doctype.hd_ticket.api import (
    get_one,
    get_ticket_customizations,
    merge_ticket,
)
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_one as get_ticket_form
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    create_customer,
    make_customer_ticket,
    make_template,
    reply_from_the_portal,
    set_default_template_visibility,
)
from helpdesk.ticket_fields import TicketFields

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
        self.assertFalse(get_one(ticket.name).get("response_by"))
        self.assertTrue(client_get("HD Ticket", ticket.name).get("response_by"))
        frappe.set_user(AGENT_EMAIL)
        self.assertTrue(get_one(ticket.name).get("response_by"))

    def test_hiding_the_contact_fields_still_returns_a_ticket(self):
        """get_one used to build the contact card out of raised_by, which hiding removes."""
        self.addCleanup(set_default_template_visibility("contact", "Agents"))
        self.addCleanup(set_default_template_visibility("raised_by", "Agents"))
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name)
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

    def test_visible_custom_fields_are_the_everyone_rows(self):
        self.addCleanup(set_default_template_visibility("priority", "Agents"))
        self.assertNotIn("priority", get_visible_custom_fields())
        set_default_template_visibility("priority", "Everyone")
        self.assertIn("priority", get_visible_custom_fields())

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

    def test_a_miscased_fieldname_cannot_be_added_to_a_template(self):
        """The DB matches case-insensitively; the forms and checks do not."""
        template = frappe.get_doc("HD Ticket Template", DEFAULT_TICKET_TEMPLATE)
        template.append("fields", {"fieldname": "status_Category"})
        with self.assertRaisesRegex(frappe.ValidationError, "does not exist"):
            template.save()

    def test_details_tab_lists_the_template_then_the_core_fields(self):
        """The order a layout editor will build on: template rows, then core."""
        self.addCleanup(set_default_template_visibility("priority", "Everyone"))
        frappe.set_user(AGENT_EMAIL)
        fields = TicketFields()
        form = [f.fieldname for f in fields.get_form()]
        details = [f.fieldname for f in fields.get_layout()]
        unlisted = [f for f in CORE_TICKET_FIELDS if f not in form]
        self.assertIn("priority", form)
        self.assertEqual(details, form + unlisted)

    def test_agent_customizations_follow_the_ticket_template(self):
        """The details tab must use the opened ticket's template, not Default."""
        self.addCleanup(set_default_template_visibility("priority", "Everyone"))
        template = make_template(
            f"Agent Customizations {frappe.generate_hash(length=6)}",
            [
                {
                    "fieldname": "summary",
                    "visible_to": "Agents",
                    "required": 1,
                    "placeholder": "Summarize the issue",
                }
            ],
        )
        ticket = make_customer_ticket(
            self, CUSTOMER_EMAIL, template=template.name, summary="A custom summary"
        )
        frappe.set_user(AGENT_EMAIL)

        rows = get_ticket_customizations(ticket=ticket.name)["fields"]

        self.assertEqual(rows[0].fieldname, "summary")
        self.assertEqual(rows[0].required, 1)
        self.assertEqual(rows[0].placeholder, "Summarize the issue")
        self.assertEqual(get_ticket_customizations()["fields"][0].fieldname, "priority")

    def test_agent_workflow_columns_hidden_from_customers(self):
        """_user_tags and friends bypass permission levels and must never reach the portal."""
        ticket = make_customer_ticket(self, CUSTOMER_EMAIL)
        frappe.db.set_value(
            "HD Ticket",
            ticket.name,
            {"_user_tags": ",Internal Tag", "_assign": '["agent@test.com"]'},
        )

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name)
        self.assertFalse(result.get("_user_tags"))
        self.assertFalse(result.get("_assign"))

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
        rows = get_one(ticket.name)["template"]["fields"]
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
        """set_customer_field only narrows a row the form already allowed."""
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
