import copy
import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.auth import authenticate
from helpdesk.integrations.whatsapp.outgoing import NEW_TICKET_BUTTON, NO_TICKET_BUTTON
from helpdesk.integrations.whatsapp.setup import setup_whatsapp
from helpdesk.integrations.whatsapp.test_utils import (
    META_REQUEST,
    make_number,
    make_whatsapp_account,
    mock_meta,
    press_button,
    react_to,
    receive_message,
    requires_whatsapp,
)
from helpdesk.test_utils import create_agent, make_ticket, unique_email

WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


@requires_whatsapp
class IncomingTestCase(IntegrationTestCase):
    """Intake helpers shared by the inbound test files."""

    def setUp(self) -> None:
        self.meta = self.enterContext(mock_meta())
        self.account = make_whatsapp_account()
        self.number = make_number()

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def receive(
        self, text: str, number: str | None = None, account: str | None = None, **msg
    ):
        return receive_message(
            number or self.number, text, account or self.account, **msg
        )

    def press(self, button: str):
        return press_button(self.number, self.account, self.prompts()[-1].name, button)

    def profile(self) -> str:
        return frappe.db.get_value(
            "WA Profile",
            {"phone_number": f"+{self.number}", "whatsapp_account": self.account},
        )

    def prompts(self) -> list:
        return frappe.get_all(
            "WA Message",
            filters=[
                ["WA Message", "direction", "=", "Outgoing"],
                ["WA Message", "to", "=", self.profile()],
                ["WA Message Interactive Button", "button_id", "=", NEW_TICKET_BUTTON],
            ],
            fields=["name", "reference_docname"],
            order_by="creation asc",
        )

    @staticmethod
    def ticket_of(message) -> str:
        return message.reference_docname

    @staticmethod
    def close(ticket: str) -> str:
        doc = frappe.get_doc("HD Ticket", ticket)
        doc.status = "Closed"
        doc.save()
        return ticket

    @staticmethod
    def make_contact(email: str, phone: str, primary_field: str) -> str:
        contact = frappe.get_doc({"doctype": "Contact", "first_name": "Known"})
        contact.add_email(email, is_primary=1)
        contact.add_phone(phone, **{primary_field: 1})
        return contact.insert(ignore_permissions=True).name

    @staticmethod
    def clear_assignment_rule_cache() -> None:
        from frappe.cache_manager import clear_doctype_map

        clear_doctype_map("Assignment Rule", "HD Ticket")


class TestWhatsAppIncoming(IncomingTestCase):
    def test_first_message_from_a_guest_webhook_opens_a_whatsapp_ticket(self) -> None:
        frappe.db.set_value("User", "Guest", "user_type", "Website User")
        frappe.set_user("Guest")
        with patch.dict(frappe.conf, {"block_endpoints": 1}):
            with patch.dict(
                frappe.form_dict, {"cmd": "whatsapp.whatsapp.webhook.handler"}
            ):
                authenticate()
        self.post_webhook("<b>Order</b> late\nplease help")
        self.assertEqual(frappe.session.user, "Guest")
        frappe.set_user("Administrator")

        message = frappe.get_last_doc("WA Message", {"to": self.profile()})
        self.assertEqual((message.direction, message.docstatus), ("Incoming", 1))
        ticket = frappe.get_doc("HD Ticket", message.reference_docname)
        self.assertEqual(
            (ticket.source, ticket.subject),
            ("WhatsApp", "<b>Order</b> late please help"),
        )
        self.assertFalse(ticket.raised_by)
        self.assertIn(
            "&lt;b&gt;Order&lt;/b&gt; late<br>please help", ticket.description
        )
        self.assertIsNotNone(ticket.last_customer_response)
        contact = frappe.get_doc("Contact", ticket.contact)
        self.assertEqual(contact.first_name, "Webhook Customer")
        self.assertEqual(contact.mobile_no, f"+{self.number}")
        self.assertFalse(
            frappe.db.exists("Communication", {"reference_name": ticket.name})
        )

    def test_subject_is_one_line_of_at_most_140_characters(self) -> None:
        long_word = "https://example.com/" + "a" * 200
        for text in (long_word, "word " * 60):
            ticket = self.ticket_of(self.receive(text, number=make_number()))
            subject = frappe.db.get_value("HD Ticket", ticket, "subject")
            self.assertEqual(len(subject), 140)
            self.assertTrue(subject.startswith(text[:20]) and subject.endswith("…"))

    def test_media_first_message_is_named_after_the_sender(self) -> None:
        image = {"id": "media-1", "mime_type": "image/jpeg"}
        ticket = self.ticket_of(self.receive("", type="image", image=image))
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket, ["subject", "description"]),
            ("Message on WhatsApp from Test Customer", ""),
        )

    def test_known_contact_matches_on_phone_or_mobile_and_skips_emails(self) -> None:
        for field in ("is_primary_phone", "is_primary_mobile_no"):
            number = make_number()
            national = number[2:]
            email = unique_email("whatsapp-known")
            contact = self.make_contact(
                email, f"(+91) {national[:5]}-{national[5:]}", field
            )
            email_ticket = make_ticket(raised_by=email, contact=contact).name
            contacts = frappe.db.count("Contact")
            with self.change_settings(
                "HD Settings",
                {
                    "send_acknowledgement_email": 1,
                    "enable_email_ticket_feedback": 1,
                    "send_email_feedback_on_status": "Resolved",
                },
            ):
                ticket = frappe.get_doc(
                    "HD Ticket", self.ticket_of(self.receive("Hi", number=number))
                )
                ticket.status = "Resolved"
                ticket.save()
            self.assertEqual((ticket.contact, ticket.raised_by), (contact, email))
            self.assertEqual(frappe.db.count("Contact"), contacts)
            self.assertNotEqual(ticket.name, email_ticket)
            self.assertFalse(
                frappe.db.exists("Email Queue", {"reference_name": ticket.name})
            )

    def test_next_messages_append_and_reopen_paused_or_resolved_tickets(self) -> None:
        agent = create_agent(unique_email("whatsapp-reopen")).name
        ticket = frappe.get_doc("HD Ticket", self.ticket_of(self.receive("Help")))
        ticket.assign_agent(agent)
        for status in ("Replied", "Resolved"):
            ticket.reload()
            ticket.status = status
            ticket.save()
            last_response = ticket.last_customer_response
            self.assertEqual(self.ticket_of(self.receive("Still broken")), ticket.name)
            ticket.reload()
            self.assertEqual(ticket.status, ticket.ticket_reopen_status)
            self.assertGreater(ticket.last_customer_response, last_response)
        self.assertTrue(
            frappe.db.exists(
                "Notification Log",
                {
                    "type": "Ticket Reopened",
                    "document_name": ticket.name,
                    "for_user": agent,
                },
            )
        )
        self.assertEqual(frappe.db.count("HD Ticket", {"contact": ticket.contact}), 1)

    def test_closed_ticket_prompts_once_and_holds_messages(self) -> None:
        closed = self.close(self.ticket_of(self.receive("First problem")))
        held = [self.receive("New problem"), self.receive("More detail")]

        prompts = self.prompts()
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0].reference_docname, closed)
        prompt = frappe.get_doc("WA Message", prompts[0].name)
        self.assertEqual(
            prompt.message,
            f"Your previous ticket #{closed} is closed. Do you want to raise a new one?",
        )
        self.assertEqual(
            [(row.button_id, row.title) for row in prompt.interactive_buttons],
            [
                (NEW_TICKET_BUTTON, "Create new ticket"),
                (NO_TICKET_BUTTON, "No, thanks"),
            ],
        )
        payload = self.meta.call_args.kwargs["json"]
        self.assertEqual(payload["type"], "interactive")
        self.assertEqual([message.reference_docname for message in held], [None, None])
        self.assertEqual(frappe.db.get_value("HD Ticket", closed, "status"), "Closed")

    def test_create_new_ticket_takes_every_held_message(self) -> None:
        closed = self.close(self.ticket_of(self.receive("First problem")))
        held = [self.receive("New problem"), self.receive("More detail")]
        answer = self.press(NEW_TICKET_BUTTON)

        ticket = frappe.get_doc("HD Ticket", answer.reference_docname)
        self.assertNotEqual(ticket.name, closed)
        self.assertEqual(ticket.subject, "New problem")
        self.assertEqual(ticket.description, "New problem<br>More detail")
        self.assertEqual(answer.message, "Create new ticket")
        for message in held:
            message.reload()
            self.assertEqual(message.reference_docname, ticket.name)
        self.assertEqual(self.ticket_of(self.receive("Thanks")), ticket.name)
        self.assertEqual(self.ticket_of(self.press(NEW_TICKET_BUTTON)), ticket.name)

    def test_no_thanks_acknowledges_and_the_next_message_prompts_again(self) -> None:
        closed = self.close(self.ticket_of(self.receive("First problem")))
        declined = self.receive("Never mind")
        self.press(NO_TICKET_BUTTON)

        acknowledgement = frappe.get_last_doc(
            "WA Message", {"direction": "Outgoing", "to": self.profile()}
        )
        self.assertFalse(acknowledgement.interactive_buttons)
        self.assertIn("won't open a new ticket", acknowledgement.message)
        self.assertEqual(acknowledgement.reference_docname, closed)
        declined.reload()
        self.assertIsNone(declined.reference_docname)

        self.receive("Actually it broke again")
        self.assertEqual(len(self.prompts()), 2)
        ticket = self.ticket_of(self.press(NEW_TICKET_BUTTON))
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket, "subject"),
            "Actually it broke again",
        )

    def test_typed_reply_quoting_the_prompt_is_held_not_an_answer(self) -> None:
        self.close(self.ticket_of(self.receive("First problem")))
        self.receive("New problem")
        prompt = frappe.get_doc("WA Message", self.prompts()[-1].name)
        typed = self.receive("Yes please", context={"id": prompt.message_id})
        self.assertIsNone(typed.reference_docname)
        self.assertEqual(len(self.prompts()), 1)

    def test_reactions_follow_the_reacted_message_and_never_reopen(self) -> None:
        first = self.receive("Old problem")
        closed = self.close(first.reference_docname)
        self.receive("New problem")
        active = self.ticket_of(self.press(NEW_TICKET_BUTTON))

        reaction = react_to(self.number, self.account, first.message_id, "👍")
        self.assertEqual(reaction.reference_docname, closed)
        # a retraction, Meta's empty emoji, follows too and is never a ticket's latest message
        react_to(self.number, self.account, first.message_id, "")
        self.assertEqual(frappe.db.get_value("HD Ticket", closed, "status"), "Closed")
        self.assertEqual(self.ticket_of(self.receive("Any update?")), active)

    def test_merged_tickets_route_to_the_merge_target(self) -> None:
        source = self.ticket_of(self.receive("Duplicate"))
        target = self.ticket_of(self.receive("Original", number=make_number()))
        frappe.db.set_value(
            "HD Ticket", source, {"is_merged": 1, "merged_with": target}
        )
        self.assertEqual(self.ticket_of(self.receive("Follow up")), target)

    def test_each_business_number_keeps_its_own_ticket(self) -> None:
        first = frappe.get_doc(
            "HD Ticket", self.ticket_of(self.receive("Sales question"))
        )
        other = self.receive("Support question", account=make_whatsapp_account())
        second = frappe.get_doc("HD Ticket", other.reference_docname)
        self.assertNotEqual(first.name, second.name)
        self.assertEqual(first.contact, second.contact)
        self.assertEqual(self.ticket_of(self.receive("Sales again")), first.name)

    def test_a_meta_failure_on_the_prompt_still_stores_the_message(self) -> None:
        self.close(self.ticket_of(self.receive("First problem")))
        with patch(META_REQUEST, side_effect=Exception("Meta is down")):
            message = self.receive("Hello?")
        self.assertTrue(frappe.db.exists("WA Message", message.name))
        self.assertEqual(self.prompts(), [])
        self.receive("Hello again")
        self.assertEqual(len(self.prompts()), 1)

    def test_another_apps_relink_never_takes_a_message_off_its_ticket(self) -> None:
        hooks = copy.deepcopy(frappe.get_doc_hooks())
        validate = hooks["WA Message"].setdefault("validate", [])
        validate.append(f"{__name__}.relink_to_contact")
        with patch.object(frappe.local, "doc_events_hooks", hooks):
            message = self.receive("Help")
        self.assertEqual(message.reference_doctype, "HD Ticket")
        self.assertTrue(frappe.db.exists("HD Ticket", message.reference_docname))

    def test_assignment_rules_assign_new_whatsapp_tickets(self) -> None:
        agent = create_agent(unique_email("whatsapp-assignee")).name
        frappe.db.after_rollback.add(self.clear_assignment_rule_cache)
        frappe.get_doc(
            {
                "doctype": "Assignment Rule",
                "name": "WhatsApp Intake Test",
                "document_type": "HD Ticket",
                "description": "Assigns WhatsApp tickets",
                "assign_condition": "source == 'WhatsApp'",
                "rule": "Round Robin",
                "priority": 99,
                "assignment_days": [{"day": day} for day in WEEKDAYS],
                "users": [{"user": agent}],
            }
        ).insert(ignore_permissions=True)
        ticket = self.ticket_of(self.receive("Assign me"))
        self.assertIn(
            agent,
            json.loads(frappe.db.get_value("HD Ticket", ticket, "_assign") or "[]"),
        )
        self.assertTrue(
            frappe.db.exists(
                "Notification Log",
                {"type": "Assignment", "document_name": ticket, "for_user": agent},
            )
        )

    def test_whatsapp_source_is_added_once_and_never_removed(self) -> None:
        for hook in ("after_migrate", "after_app_install"):
            self.assertIn(
                "helpdesk.integrations.whatsapp.setup.setup_whatsapp",
                frappe.get_hooks(hook),
            )
        setup_whatsapp()
        setup_whatsapp("whatsapp")
        setters = frappe.get_all(
            "Property Setter",
            {"doc_type": "HD Ticket", "field_name": "source"},
            pluck="value",
        )
        self.assertEqual(setters, ["Email\nPortal\nWhatsApp"])
        with patch("frappe.get_installed_apps", return_value=["frappe", "helpdesk"]):
            setup_whatsapp()
        self.assertIn(
            "WhatsApp", frappe.get_meta("HD Ticket").get_field("source").options
        )

    def test_agents_may_only_read_conversations_and_templates(self) -> None:
        setup_whatsapp("whatsapp")
        agent = create_agent(unique_email("whatsapp-rights")).name
        for doctype in ("WA Message", "WA Template"):
            self.assertTrue(frappe.has_permission(doctype, "read", user=agent))
        for right in ("write", "create", "submit"):
            self.assertFalse(frappe.has_permission("WA Message", right, user=agent))
        self.assertFalse(frappe.has_permission("WA Profile", "read", user=agent))
        self.assertFalse(frappe.has_permission("WA Template", "write", user=agent))
        self.assertFalse(frappe.has_permission("WA Account", "read", user=agent))

    def post_webhook(self, text: str) -> None:
        """Deliver a text the way Meta does, through the whatsapp app's webhook."""
        from whatsapp.whatsapp.webhook import _receive

        phone_id = frappe.db.get_value("WA Account", self.account, "phone_id")
        value = {
            "metadata": {"phone_number_id": phone_id},
            "contacts": [
                {"profile": {"name": "Webhook Customer"}, "wa_id": self.number}
            ],
            "messages": [
                {
                    "from": self.number,
                    "id": f"wamid.{self.number}",
                    "type": "text",
                    "text": {"body": text},
                }
            ],
        }
        payload = {"entry": [{"changes": [{"field": "messages", "value": value}]}]}
        with (
            self.change_settings("WA Settings", {"webhook_secret": ""}),
            patch.object(frappe.local, "form_dict", frappe._dict(payload)),
        ):
            _receive()


def relink_to_contact(doc, method: str | None = None) -> None:
    """Stands in for CRM's validate, which links messages to its own records."""
    doc.reference_doctype, doc.reference_docname = "Contact", "Anyone"
