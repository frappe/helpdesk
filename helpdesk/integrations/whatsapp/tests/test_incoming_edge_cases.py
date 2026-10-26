import random
from unittest.mock import patch

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from helpdesk.integrations.whatsapp.outgoing import NEW_TICKET_BUTTON, NO_TICKET_BUTTON
from helpdesk.integrations.whatsapp.setup import add_whatsapp_source
from helpdesk.integrations.whatsapp.test_utils import (
    META_REQUEST,
    make_number,
    press_button,
    requires_whatsapp,
)
from helpdesk.integrations.whatsapp.tests.test_incoming import IncomingTestCase
from helpdesk.test_utils import unique_email


@requires_whatsapp
class TestWhatsAppIncomingEdgeCases(IncomingTestCase):
    def test_a_mandatory_ticket_field_never_blocks_intake(self) -> None:
        self.customize_ticket("agent_group", "reqd", "1", "Check")
        ticket = self.ticket_of(self.receive("First"))
        self.assertTrue(ticket)
        self.assertEqual(self.ticket_of(self.receive("Second")), ticket)

    def test_a_deleted_ticket_takes_its_messages_so_its_reused_name_starts_empty(
        self,
    ) -> None:
        first_customer = self.number
        deleted = self.ticket_of(self.receive("My card number is 4111"))
        frappe.delete_doc("HD Ticket", deleted)
        self.assertFalse(frappe.db.exists("WA Message", {"reference_docname": deleted}))

        self.number = make_number()
        ticket = self.ticket_of(self.receive("Hello"))
        self.assertEqual(ticket, deleted)
        thread = frappe.get_all(
            "WA Message", {"reference_docname": ticket}, pluck="message"
        )
        self.assertEqual(thread, ["Hello"])
        again = self.ticket_of(self.receive("Me again", number=first_customer))
        self.assertNotEqual(again, ticket)

    def test_contacts_match_the_full_number_not_a_shared_national_number(self) -> None:
        indian = make_number()
        singapore_national = f"9{random.randint(10**6, 10**7 - 1)}"
        strangers = {
            indian: f"+44 {indian[2:]}",
            f"65{singapore_national}": f"+91 {singapore_national}89",
        }
        for sender, stored in strangers.items():
            stranger = self.make_contact(
                unique_email("stranger"), stored, "is_primary_mobile_no"
            )
            ticket = self.ticket_of(self.receive("Hi", number=sender))
            self.assertNotEqual(
                frappe.db.get_value("HD Ticket", ticket, "contact"), stranger
            )

        sender = make_number()
        local = self.make_contact(
            unique_email("local"), sender[2:], "is_primary_mobile_no"
        )
        ticket = self.ticket_of(self.receive("Hi", number=sender))
        self.assertEqual(frappe.db.get_value("HD Ticket", ticket, "contact"), local)

    def test_custom_source_options_survive_migrate(self) -> None:
        for custom, expected in (
            ("Email\nPortal\nWhatsApp\nPhone", "Email\nPortal\nWhatsApp\nPhone"),
            ("Email\nPortal\nPhone", "Email\nPortal\nPhone\nWhatsApp"),
        ):
            self.customize_ticket("source", "options", custom, "Text")
            add_whatsapp_source()
            self.assertEqual(
                frappe.get_meta("HD Ticket").get_field("source").options, expected
            )

    def test_held_messages_another_app_relinked_still_join_the_new_ticket(
        self,
    ) -> None:
        closed = self.close(self.ticket_of(self.receive("First problem")))
        held = self.receive("New problem")
        # CRM's validate links messages from known numbers to its Lead
        contact = frappe.db.get_value("HD Ticket", closed, "contact")
        frappe.db.set_value(
            "WA Message",
            held.name,
            {"reference_doctype": "Contact", "reference_docname": contact},
        )
        ticket = self.ticket_of(self.press(NEW_TICKET_BUTTON))
        held.reload()
        self.assertEqual(held.reference_docname, ticket)
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket, "subject"), "New problem"
        )

    def test_a_prompt_created_ticket_closed_without_reply_prompts_again(
        self,
    ) -> None:
        self.close(self.ticket_of(self.receive("First problem")))
        self.receive("Second problem")
        second = self.close(self.ticket_of(self.press(NEW_TICKET_BUTTON)))
        third = self.receive("Third problem")

        prompts = self.prompts()
        self.assertEqual(len(prompts), 2)
        self.assertIn(second, [prompt.reference_docname for prompt in prompts])
        ticket = self.ticket_of(self.press(NEW_TICKET_BUTTON))
        third.reload()
        self.assertEqual(third.reference_docname, ticket)
        self.assertNotEqual(ticket, second)

    def test_reopening_the_closed_ticket_takes_its_held_messages(self) -> None:
        for follow_up in (
            lambda: self.receive("Hello?"),
            lambda: self.press(NO_TICKET_BUTTON),
        ):
            self.number = make_number()
            closed = self.close(self.ticket_of(self.receive("First problem")))
            held = self.receive("Need help again")
            reopened = frappe.get_doc("HD Ticket", closed)
            reopened.status = "Open"
            reopened.save()
            self.assertEqual(self.ticket_of(follow_up()), closed)
            held.reload()
            self.assertEqual(held.reference_docname, closed)

    def test_a_failed_no_thanks_acknowledgement_still_ends_the_prompt(self) -> None:
        self.close(self.ticket_of(self.receive("First problem")))
        self.receive("Again")
        with patch(META_REQUEST, side_effect=Exception("Meta is down")):
            self.press(NO_TICKET_BUTTON)
        self.receive("Still need help")
        self.assertEqual(len(self.prompts()), 2)

    def test_a_stale_button_from_an_older_prompt_opens_nothing_new(self) -> None:
        self.close(self.ticket_of(self.receive("First problem")))
        self.receive("Second problem")
        stale = self.prompts()[-1].name
        active = self.ticket_of(self.press(NEW_TICKET_BUTTON))
        again = press_button(self.number, self.account, stale, NO_TICKET_BUTTON)
        self.assertEqual(again.reference_docname, active)
        self.assertEqual(frappe.db.count("HD Ticket", {"contact": self.contact()}), 2)

    def test_a_profile_name_with_angle_brackets_still_opens_a_ticket(self) -> None:
        for profile_name, first_name in (("Bob <3", "Bob 3"), ("<>", None)):
            self.number = make_number()
            ticket = self.ticket_of(self.receive("Hi", profile_name=profile_name))
            contact = frappe.db.get_value("HD Ticket", ticket, "contact")
            self.assertEqual(
                frappe.db.get_value("Contact", contact, "first_name"),
                first_name or f"+{self.number}",
            )

    def contact(self) -> str:
        message = frappe.get_last_doc(
            "WA Message", {"to": self.profile(), "direction": "Incoming"}
        )
        return frappe.db.get_value("HD Ticket", message.reference_docname, "contact")

    def customize_ticket(
        self, fieldname: str, property: str, value: str, property_type: str
    ) -> None:
        frappe.db.after_rollback.add(lambda: frappe.clear_cache(doctype="HD Ticket"))
        make_property_setter(
            "HD Ticket",
            fieldname,
            property,
            value,
            property_type,
            validate_fields_for_doctype=False,
        )
        frappe.clear_cache(doctype="HD Ticket")
