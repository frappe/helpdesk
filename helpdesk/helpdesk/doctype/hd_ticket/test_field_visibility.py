import frappe
from frappe.client import get as client_get
from frappe.permissions import update_permission_property
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import get_filterable_fields, get_list_data
from helpdesk.consts import DEFAULT_TICKET_TEMPLATE, TICKET_INTERNAL_FIELD_PERMLEVEL
from helpdesk.field_visibility import fields_visible_to
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
        create_agent(AGENT_EMAIL)
        self.contact = create_contact("FV Customer", CUSTOMER_EMAIL)["contact"]

    def tearDown(self):
        frappe.set_user("Administrator")

    def make_customer_ticket(self, **values):
        ticket = make_ticket(raised_by=CUSTOMER_EMAIL, **values)
        self.addCleanup(frappe.delete_doc, "HD Ticket", ticket.name, force=True)
        return ticket

    def show_to(self, fieldname: str, visible_to: str):
        self.addCleanup(set_default_template_visibility(fieldname, visible_to))

    def test_agents_only_field_is_stripped_for_customers(self):
        # response_by is at the customer-readable level; visible_to alone hides it
        self.show_to("response_by", "Agents")
        ticket = self.make_customer_ticket()

        frappe.set_user(CUSTOMER_EMAIL)
        self.assertFalse(
            get_one(ticket.name, is_customer_portal=True).get("response_by")
        )
        frappe.set_user(AGENT_EMAIL)
        self.assertTrue(get_one(ticket.name).get("response_by"))

    def test_customers_only_field_is_stripped_for_agents(self):
        self.show_to("priority", "Customers")
        ticket = self.make_customer_ticket()

        frappe.set_user(AGENT_EMAIL)
        self.assertFalse(get_one(ticket.name).get("priority"))
        frappe.set_user(CUSTOMER_EMAIL)
        self.assertTrue(get_one(ticket.name, is_customer_portal=True).get("priority"))

    def test_visible_to_hides_from_helpdesk_pages_not_from_the_framework(self):
        """The tier is layout, not a permission. Raising the permlevel in Customize
        Form is what withholds a value from every path."""
        self.show_to("priority", "Agents")
        ticket = self.make_customer_ticket()

        frappe.set_user(CUSTOMER_EMAIL)
        self.assertFalse(get_one(ticket.name, is_customer_portal=True).get("priority"))
        self.assertTrue(client_get("HD Ticket", ticket.name).get("priority"))

    def test_a_save_after_the_read_strip_keeps_the_hidden_value(self):
        """A hidden field is absent from the payload, so a whole-document save would
        write that absence back over the stored value."""
        self.show_to("priority", "Customers")
        ticket = self.make_customer_ticket(priority="High")

        frappe.set_user(AGENT_EMAIL)
        doc = frappe.get_doc("HD Ticket", ticket.name)
        doc.apply_fieldlevel_read_permissions()
        doc.subject = "edited by the agent"
        doc.save()

        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "priority"), "High"
        )

    def test_hiding_the_contact_fields_still_returns_a_ticket(self):
        """With no contact to fall back on, get_one used to build the contact
        card out of `raised_by` — which hiding it takes away."""
        self.show_to("contact", "Agents")
        self.show_to("raised_by", "Agents")
        ticket = self.make_customer_ticket()

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_one(ticket.name, is_customer_portal=True)
        self.assertEqual(result["contact"]["name"], "")
        self.assertFalse(result["contact"]["email_id"])

    def drop_agent_write_at_internal_level(self):
        """A site whose Agent role never reached the internal level."""
        self.addCleanup(frappe.clear_cache)
        self.addCleanup(frappe.db.delete, "Custom DocPerm", {"parent": "HD Ticket"})
        update_permission_property(
            "HD Ticket",
            "Agent",
            TICKET_INTERNAL_FIELD_PERMLEVEL,
            "write",
            0,
            validate=False,
        )
        frappe.clear_cache()

    def test_merge_records_the_link_without_write_at_the_internal_level(self):
        """The source closes either way, so dropping the link with it leaves a
        closed ticket and nothing to say where it went."""
        self.drop_agent_write_at_internal_level()
        source = self.make_customer_ticket()
        target = self.make_customer_ticket()

        frappe.set_user(AGENT_EMAIL)
        merge_ticket(source=source.name, target=target.name)

        self.assertEqual(
            frappe.db.get_value("HD Ticket", source.name, "merged_with"), target.name
        )

    def reply_from_the_portal(self, status: str):
        ticket = self.make_customer_ticket()
        frappe.db.set_value("HD Ticket", ticket.name, "status", status)
        frappe.set_user(CUSTOMER_EMAIL)
        frappe.get_doc("HD Ticket", ticket.name).create_communication_via_contact(
            "it is happening again"
        )
        frappe.set_user("Administrator")
        return frappe.db.get_value("HD Ticket", ticket.name, "status")

    def test_a_portal_reply_reopens_a_ticket_the_agent_answered(self):
        """Replied is where every ticket sits once an agent has responded, so
        the edit guard must not treat the reopen as a customer edit."""
        for status in ("Replied", "Resolved"):
            with self.subTest(status=status):
                self.assertEqual(self.reply_from_the_portal(status), "Open")

    def test_a_portal_reply_cannot_reopen_a_closed_ticket(self):
        with self.assertRaises(frappe.PermissionError):
            self.reply_from_the_portal("Closed")

    def raise_priority_beyond_customers(self):
        """What the template's own warning tells an admin to do to hide a field
        from every path, not just helpdesk's pages."""
        frappe.make_property_setter(
            {
                "doctype": "HD Ticket",
                "fieldname": "priority",
                "property": "permlevel",
                "value": TICKET_INTERNAL_FIELD_PERMLEVEL,
                "property_type": "Int",
            },
            is_system_generated=False,
        )
        self.addCleanup(frappe.clear_cache)
        self.addCleanup(
            frappe.db.delete,
            "Property Setter",
            {"doc_type": "HD Ticket", "field_name": "priority"},
        )
        frappe.clear_cache()

    def test_a_column_the_query_cannot_return_is_not_drawn(self):
        """A header with no data under it on every row, forever."""
        self.make_customer_ticket(priority="High")
        self.raise_priority_beyond_customers()

        frappe.set_user(CUSTOMER_EMAIL)
        result = get_list_data(
            "HD Ticket",
            rows=["subject", "priority"],
            columns=[{"key": "subject"}, {"key": "priority"}],
        )
        self.assertNotIn("priority", [c.get("key") for c in result["columns"]])
        self.assertNotIn("priority", result["rows"])

    def test_a_filter_the_query_would_refuse_is_not_offered(self):
        self.raise_priority_beyond_customers()
        frappe.set_user(CUSTOMER_EMAIL)
        offered = [f.get("fieldname") for f in get_filterable_fields("HD Ticket")]
        self.assertNotIn("priority", offered)

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

    def test_hiding_warns_only_while_the_api_still_serves_the_field(self):
        """The warning asks the admin to raise the level in Customize Form, so
        it has to stop once they have — otherwise it is nagging about nothing."""
        frappe.clear_messages()
        self.show_to("priority", "Agents")
        self.assertTrue(any("Priority" in str(m) for m in frappe.message_log))

        self.raise_priority_beyond_customers()
        frappe.clear_messages()
        frappe.get_doc("HD Ticket Template", "Default").save(ignore_permissions=True)
        self.assertFalse(any("Priority" in str(m) for m in frappe.message_log))

    def test_the_default_template_cannot_be_renamed(self):
        """Renaming it would leave every visible_to lookup finding nothing."""
        with self.assertRaises(frappe.PermissionError):
            frappe.rename_doc("HD Ticket Template", "Default", "Renamed Default")

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

    def test_agents_only_row_is_absent_from_the_ticket_template_rows(self):
        """The portal draws every row it is handed, so the label leaks even once
        get_one has stripped the value off the ticket itself."""
        self.show_to("priority", "Everyone")
        self.show_to("response_by", "Agents")
        ticket = self.make_customer_ticket()

        frappe.set_user(CUSTOMER_EMAIL)
        rows = get_one(ticket.name, is_customer_portal=True)["template"]["fields"]
        self.assertEqual(["priority"], [row["fieldname"] for row in rows])
        # nothing ships the tier to the client, so no page can re-filter on it
        self.assertNotIn("visible_to", rows[0])

        frappe.set_user(AGENT_EMAIL)
        rows = get_one(ticket.name)["template"]["fields"]
        self.assertIn("response_by", [row["fieldname"] for row in rows])

    def test_agents_only_row_is_absent_from_the_new_ticket_form(self):
        """The portal and the agent desk render the same form off this payload."""
        self.show_to("priority", "Everyone")
        self.show_to("response_by", "Agents")

        frappe.set_user(CUSTOMER_EMAIL)
        fields = get_ticket_form(DEFAULT_TICKET_TEMPLATE)["fields"]
        self.assertEqual(["priority"], [field.fieldname for field in fields])

        frappe.set_user(AGENT_EMAIL)
        fields = get_ticket_form(DEFAULT_TICKET_TEMPLATE)["fields"]
        self.assertIn("response_by", [field.fieldname for field in fields])

    def link_to_two_customers(self):
        """A portal contact who has to pick which customer a ticket is for."""
        for name in ("FV Customer One", "FV Customer Two"):
            customer = create_customer(name, [{"contact_name": self.contact}])
            self.addCleanup(frappe.delete_doc, "HD Customer", customer.name, force=True)

    def test_a_multi_customer_contact_still_gets_a_required_customer_field(self):
        """set_customer_field only narrows a row get_fields_meta already allowed,
        so it has no visibility of its own to restore."""
        self.show_to("customer", "Everyone")
        self.link_to_two_customers()
        setting = "auto_set_customer_from_contact"
        original = frappe.db.get_single_value("HD Settings", setting)
        frappe.db.set_single_value("HD Settings", setting, 1)  # nosemgrep
        self.addCleanup(frappe.db.set_single_value, "HD Settings", setting, original)

        frappe.set_user(CUSTOMER_EMAIL)
        fields = get_ticket_form(DEFAULT_TICKET_TEMPLATE)["fields"]
        customer_field = next(f for f in fields if f.fieldname == "customer")
        self.assertTrue(customer_field.required)
