import json
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import patch

import frappe
import requests
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings
from frappe.utils import add_to_date, now_datetime, random_string

from helpdesk.integrations.whatsapp.api import (
    get_conversation,
    get_messages,
    render_saved_reply,
)
from helpdesk.integrations.whatsapp.formatting import html_to_whatsapp
from helpdesk.integrations.whatsapp.outgoing import get_first_agent_reply_on
from helpdesk.integrations.whatsapp.test_utils import (
    META_REQUEST,
    make_number,
    make_whatsapp_account,
    make_whatsapp_template,
    meta_response,
    mock_meta,
    receive_message,
    requires_whatsapp,
    sent_payloads,
)
from helpdesk.test_utils import create_agent, make_contact, make_ticket, unique_email

APP_API = "whatsapp.whatsapp.api.messages"
PORTAL_READ = "helpdesk.integrations.whatsapp.api.get_messages"


def app_api(method: str):
    from whatsapp.whatsapp.api import messages

    return getattr(messages, method)


@contextmanager
def as_request(cmd: str, **form) -> Iterator[None]:
    """Run as a request to `cmd`, which is what the access guard reads."""
    with patch.dict(frappe.form_dict, {"cmd": cmd, **form}):
        yield


@requires_whatsapp
class TestWhatsAppAgentAPI(IntegrationTestCase):
    """Agents send through the whatsapp app's endpoints; Helpdesk's hooks address and stamp."""

    def setUp(self) -> None:
        self.meta = self.enterContext(mock_meta())
        self.account = make_whatsapp_account()
        self.number = make_number()
        self.first = receive_message(self.number, "My order is late", self.account)
        self.ticket = self.first.reference_docname
        self.agent = create_agent(unique_email("whatsapp-agent")).name

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def send(self, message: str = "", ticket: str | None = None, **values) -> str:
        return app_api("send_message")(
            to=self.first.to,
            message=message,
            reference_doctype="HD Ticket",
            reference_docname=ticket or self.ticket,
            **values,
        )

    def test_text_goes_to_the_customer_from_their_business_number_and_stamps_sla(
        self,
    ) -> None:
        frappe.db.set_single_value(
            "WA Settings", "default_account", make_whatsapp_account()
        )
        with self.set_user(self.agent):
            name = app_api("send_message")(
                to="+15550100100",
                message="Looking into it",
                reference_doctype="HD Ticket",
                reference_docname=self.ticket,
            )
        sent = frappe.get_doc("WA Message", name)
        self.assertEqual(
            (
                sent.direction,
                sent.to,
                sent.whatsapp_account,
                sent.status,
                sent.docstatus,
            ),
            ("Outgoing", self.first.to, self.account, "Sent", 1),
        )
        first_responded_on = frappe.db.get_value(
            "HD Ticket", self.ticket, "first_responded_on"
        )
        self.assertIsNotNone(first_responded_on)
        self.assertEqual(get_first_agent_reply_on(self.ticket), sent.creation)
        with (
            self.freeze_time(add_to_date(now_datetime(), hours=1)),
            self.set_user(self.agent),
        ):
            self.send("Found it")
            ticket = frappe.get_doc("HD Ticket", self.ticket)
            self.assertEqual(ticket.first_responded_on, first_responded_on)
            self.assertEqual(ticket.last_agent_response, now_datetime())

    def test_agent_reply_honours_auto_update_status(self) -> None:
        settings = {"auto_update_status": 1, "update_status_to": "Replied"}
        with change_settings("HD Settings", settings), self.set_user(self.agent):
            self.send("Done")
        self.assertEqual(
            frappe.db.get_value("HD Ticket", self.ticket, "status"), "Replied"
        )

    def test_locked_ticket_sends_nothing_to_meta(self) -> None:
        lock = "helpdesk.integrations.whatsapp.outgoing.lock_ticket"
        with (
            patch(lock, side_effect=frappe.QueryTimeoutError),
            self.set_user(self.agent),
        ):
            name = self.send("Hi")
        self.assertEqual(frappe.db.get_value("WA Message", name, "status"), "Failed")
        self.assertEqual(sent_payloads(self.meta), [])

    def test_only_a_delivered_message_stamps_the_ticket(self) -> None:
        stamps = ["first_responded_on", "last_agent_response", "status"]
        settings = {"auto_update_status": 1, "update_status_to": "Replied"}
        before = frappe.db.get_value("HD Ticket", self.ticket, stamps)
        with (
            patch(META_REQUEST, side_effect=refuse_sends),
            change_settings("HD Settings", settings),
            self.set_user(self.agent),
        ):
            name = self.send("Hi")
        self.assertEqual(frappe.db.get_value("WA Message", name, "status"), "Failed")
        self.assertEqual(frappe.db.get_value("HD Ticket", self.ticket, stamps), before)
        save = "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.HDTicket.save"
        with patch(save, side_effect=frappe.ValidationError), self.set_user(self.agent):
            name = self.send("Hi again")
        # Meta delivered it, so a ticket that can't be stamped must not mark it Failed
        self.assertEqual(frappe.db.get_value("WA Message", name, "status"), "Sent")
        self.assertEqual(frappe.db.get_value("HD Ticket", self.ticket, stamps), before)

    def test_only_this_tickets_files_or_the_agents_own_upload_can_be_attached(
        self,
    ) -> None:
        other_ticket = receive_message(
            make_number(), "Hi", self.account
        ).reference_docname
        someone_elses = self.upload("theirs.png", attached=False)
        with self.set_user(self.agent):
            own = self.upload("mine.png", attached=False)
            for attach in (
                "/files/never-uploaded.png",
                self.upload("other.png", other_ticket),
                someone_elses,
            ):
                with self.assertRaises(
                    (frappe.PermissionError, frappe.DoesNotExistError)
                ):
                    self.send(attach=attach, content_type="image")
            self.send("See this", attach=self.upload("photo.png"), content_type="image")
            self.send("And this", attach=own, content_type="image")
        payload = sent_payloads(self.meta)[-2]
        self.assertEqual(
            (payload["type"], payload["image"]["caption"]), ("image", "See this")
        )
        linked = frappe.db.get_value(
            "File", {"file_url": own}, ["attached_to_doctype", "attached_to_name"]
        )
        self.assertEqual(linked, ("HD Ticket", self.ticket))
        self.assertFalse(
            frappe.db.get_value(
                "File", {"file_url": someone_elses}, "attached_to_name"
            )
        )

    def test_only_this_numbers_templates_are_offered_and_sent(self) -> None:
        own = make_whatsapp_template(whatsapp_account=self.account)
        shared = make_whatsapp_template()
        foreign = make_whatsapp_template(whatsapp_account=make_whatsapp_account())
        with self.set_user(self.agent):
            offered = get_conversation(self.ticket)["templates"]
            with self.assertRaisesRegex(frappe.ValidationError, "another WhatsApp"):
                app_api("send_template")(
                    foreign, self.first.to, "HD Ticket", self.ticket
                )
            app_api("send_template")(own, self.first.to, "HD Ticket", self.ticket)
        self.assertTrue({own, shared} <= set(offered))
        self.assertNotIn(foreign, offered)

    def test_quoted_reply_points_at_the_quoted_message(self) -> None:
        with self.set_user(self.agent):
            name = self.send("Which order?", reply_to=self.first.name)
            reply = next(
                row
                for row in app_api("get_messages")(
                    json.dumps([["HD Ticket", self.ticket]])
                )
                if row.name == name
            )
        self.assertEqual(reply["reply_to"], self.first.name)
        self.assertEqual(reply["reply_message"], "My order is late")
        self.assertEqual(
            sent_payloads(self.meta)[-1]["context"]["message_id"], self.first.message_id
        )

    def test_cannot_quote_another_tickets_message(self) -> None:
        other = receive_message(make_number(), "Hello", self.account)
        with self.set_user(self.agent), self.assertRaises(frappe.DoesNotExistError):
            self.send("Hi", reply_to=other.name)
        self.assertEqual(sent_payloads(self.meta), [])

    def test_reaction_shows_on_the_message_and_is_not_a_response(self) -> None:
        with self.set_user(self.agent):
            app_api("react_to_message")(self.first.name, "👍")
            thread = app_api("get_messages")(json.dumps([["HD Ticket", self.ticket]]))
        self.assertEqual([row.name for row in thread], [self.first.name])
        self.assertEqual(
            thread[0]["reactions"], [{"emoji": "👍", "direction": "Outgoing"}]
        )
        self.assertIsNone(
            frappe.db.get_value("HD Ticket", self.ticket, "first_responded_on")
        )
        self.assertIsNone(get_first_agent_reply_on(self.ticket))

    def test_closed_ticket_prompt_is_not_an_agent_response(self) -> None:
        frappe.db.set_value("HD Ticket", self.ticket, "status", "Closed")
        receive_message(self.number, "Hello again", self.account)
        prompt = frappe.get_last_doc("WA Message", {"direction": "Outgoing"})
        self.assertEqual((prompt.owner, len(prompt.interactive_buttons)), ("Guest", 2))
        stamps = frappe.db.get_value(
            "HD Ticket", self.ticket, ["first_responded_on", "last_agent_response"]
        )
        self.assertEqual(stamps, (None, None))
        self.assertIsNone(get_first_agent_reply_on(self.ticket))

    def test_closed_reply_window_blocks_free_form_but_not_templates(self) -> None:
        template = make_whatsapp_template()
        with (
            self.freeze_time(add_to_date(now_datetime(), hours=25)),
            self.set_user(self.agent),
        ):
            self.assertFalse(get_conversation(self.ticket)["reply_window_open"])
            for attempt in (
                lambda: self.send("Still there?"),
                lambda: self.send("Re", reply_to=self.first.name),
                lambda: app_api("react_to_message")(self.first.name, "👍"),
            ):
                self.assertRaises(frappe.ValidationError, attempt)
            name = app_api("send_template")(
                template, self.first.to, "HD Ticket", self.ticket
            )
        sent = frappe.get_doc("WA Message", name)
        self.assertEqual((sent.status, sent.whatsapp_account), ("Sent", self.account))
        self.assertEqual(
            json.loads(sent.template_body_parameters), {"subject": "My order is late"}
        )
        self.assertIsNotNone(
            frappe.db.get_value("HD Ticket", self.ticket, "first_responded_on")
        )

    def test_conversation_names_the_customer_and_the_reply_window(self) -> None:
        with self.freeze_time(add_to_date(now_datetime(), hours=23)):
            receive_message(self.number, "Any news?", self.account)
            closes_at = add_to_date(now_datetime(), hours=24)
        with (
            self.freeze_time(add_to_date(now_datetime(), hours=30)),
            self.set_user(self.agent),
        ):
            conversation = get_conversation(self.ticket)
        self.assertEqual(conversation["to"], self.first.to)
        self.assertTrue(conversation["installed"] and conversation["reply_window_open"])
        self.assertEqual(conversation["reply_window_closes_at"], closes_at)
        self.assertIsNone(conversation["business_number"])

    def test_saved_reply_renders_as_whatsapp_text(self) -> None:
        reply = frappe.get_doc(
            {
                "doctype": "HD Saved Reply",
                "title": f"Order {random_string(6)}",
                "message": "<p>Hi <strong>{{ subject }}</strong></p><ul><li><p>one</p></li></ul>",
            }
        ).insert(ignore_permissions=True)
        with self.set_user(self.agent):
            text = render_saved_reply(self.ticket, reply.name)
        self.assertEqual(text, "Hi *My order is late*\n• one")

    def test_non_whatsapp_ticket_and_empty_message_are_refused(self) -> None:
        email_ticket = make_ticket(raised_by=unique_email("email-customer")).name
        with self.set_user(self.agent):
            with self.assertRaisesRegex(
                frappe.ValidationError, "not a WhatsApp ticket"
            ):
                self.send("Hi", ticket=email_ticket)
            with self.assertRaises(frappe.ValidationError):
                self.send()
        self.assertEqual(sent_payloads(self.meta), [])

    def upload(
        self, file_name: str, ticket: str | None = None, attached: bool = True
    ) -> str:
        on_ticket = {
            "attached_to_doctype": "HD Ticket",
            "attached_to_name": ticket or self.ticket,
        }
        return (
            frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": file_name,
                    "content": random_string(32).encode(),
                    "is_private": 1,
                    **(on_ticket if attached else {}),
                }
            )
            .insert(ignore_permissions=True)
            .file_url
        )


@requires_whatsapp
class TestWhatsAppAPIPermissions(IntegrationTestCase):
    """The access guard: agents through, customers read their own ticket, guests nothing."""

    def setUp(self) -> None:
        self.meta = self.enterContext(mock_meta())
        self.account = make_whatsapp_account()
        self.customer = make_contact("whatsapp-customer")
        self.number = make_number()
        contact = frappe.get_doc("Contact", self.customer["contact"])
        contact.add_phone(f"+{self.number}", is_primary_mobile_no=1)
        contact.save(ignore_permissions=True)
        self.message = receive_message(self.number, "Need help", self.account)
        self.ticket = self.message.reference_docname

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_portal_contact_reads_only_their_own_thread(self) -> None:
        stranger = make_contact("whatsapp-stranger")["user"]
        with self.set_user(self.customer["user"]), as_request(PORTAL_READ):
            rows = get_messages(self.ticket)["messages"]
            self.assertEqual([row.name for row in rows], [self.message.name])
        with self.set_user(stranger), as_request(PORTAL_READ):
            self.assertRaises(frappe.PermissionError, get_messages, self.ticket)

    def test_a_customer_reads_only_through_the_portal_endpoint(self) -> None:
        read = app_api("get_messages")
        with self.set_user(self.customer["user"]):
            for doctype, name in (
                ("HD Ticket", self.ticket),
                ("Contact", self.customer["contact"]),
            ):
                references = json.dumps([[doctype, name]])
                with as_request(f"{APP_API}.get_messages", references=references):
                    self.assertRaises(frappe.PermissionError, read, references)

    def test_customers_and_guests_cannot_send(self) -> None:
        template = make_whatsapp_template()
        for user in (self.customer["user"], "Guest"):
            with self.set_user(user):
                for cmd, attempt in (
                    (
                        "send_message",
                        lambda: app_api("send_message")(self.message.to, "Hi"),
                    ),
                    (
                        "react_to_message",
                        lambda: app_api("react_to_message")(self.message.name, "👍"),
                    ),
                    (
                        "send_template",
                        lambda: app_api("send_template")(template, self.message.to),
                    ),
                ):
                    with as_request(f"{APP_API}.{cmd}"):
                        self.assertRaises(frappe.PermissionError, attempt)
        with self.set_user("Guest"), as_request(PORTAL_READ):
            self.assertRaises(frappe.PermissionError, get_messages, self.ticket)
        self.assertEqual(sent_payloads(self.meta), [])

    def test_agent_outside_the_tickets_team_cannot_read_or_send(self) -> None:
        agent = create_agent(unique_email("whatsapp-outsider")).name
        restricted = {
            "restrict_tickets_by_agent_group": 1,
            "do_not_restrict_tickets_without_an_agent_group": 0,
        }
        with change_settings("HD Settings", restricted), self.set_user(agent):
            listed = frappe.get_list("WA Message", filters={"name": self.message.name})
            self.assertEqual(listed, [])
            self.assertFalse(
                frappe.has_permission("WA Message", "read", self.message.name)
            )
            self.assertRaises(frappe.PermissionError, frappe.get_list, "WA Profile")
            for attempt in (
                lambda: get_conversation(self.ticket),
                lambda: app_api("get_messages")(
                    json.dumps([["HD Ticket", self.ticket]])
                ),
                lambda: app_api("send_message")(
                    self.message.to,
                    "Hi",
                    reference_doctype="HD Ticket",
                    reference_docname=self.ticket,
                ),
            ):
                self.assertRaises(frappe.PermissionError, attempt)

    def test_agents_message_customers_only_from_their_tickets(self) -> None:
        agent = create_agent(unique_email("whatsapp-sender")).name
        frappe.db.set_single_value("WA Settings", "default_account", self.account)
        raw_send = frappe.get_doc(
            {
                "doctype": "WA Message",
                "direction": "Outgoing",
                "to": self.message.to,
                "message": "Hi",
            }
        )
        with self.set_user(agent):
            self.assertRaises(
                frappe.PermissionError, app_api("send_message"), make_number(), "Hi"
            )
            with self.assertRaisesRegex(frappe.PermissionError, "from their ticket"):
                app_api("send_message")(
                    make_number(),
                    "Hi",
                    reference_doctype="Contact",
                    reference_docname=self.customer["contact"],
                )
            self.assertRaises(frappe.PermissionError, raw_send.insert)
        self.assertEqual(sent_payloads(self.meta), [])

    def test_calls_about_other_doctypes_are_left_to_the_app(self) -> None:
        manager = frappe.get_doc(
            {
                "doctype": "User",
                "email": unique_email("whatsapp-admin"),
                "first_name": "Admin",
                "roles": [{"role": "System Manager"}],
            }
        ).insert(ignore_permissions=True)
        cmd = "whatsapp.whatsapp.whatsapp.doctype.wa_template.wa_template.get_sendable_templates"
        from whatsapp.whatsapp.doctype.wa_template.wa_template import (
            get_sendable_templates,
        )

        with self.set_user(manager.name):
            with as_request(cmd, reference_doctype="Contact"):
                self.assertIsInstance(get_sendable_templates("Contact"), list)
            with as_request(cmd, reference_doctype="HD Ticket"):
                self.assertRaises(
                    frappe.PermissionError, get_sendable_templates, "HD Ticket"
                )


def refuse_sends(method: str, endpoint: str, **kwargs) -> dict:
    if method == "POST" and endpoint.endswith("/messages"):
        raise requests.HTTPError("Meta refused the message")
    return meta_response(method, endpoint, **kwargs)


class TestWhatsAppFormatting(IntegrationTestCase):
    def test_editor_html_becomes_whatsapp_markup(self) -> None:
        html = (
            "<p>Hello <strong>Ana </strong>, <em>thanks</em> <s>old</s> <code>x=1</code></p>"
            "<p></p><p>Line<br>break &amp; <a href='https://example.com/kb'>our guide</a></p>"
            "<ul><li><p>first</p></li><li>second</li></ul><p>Bye</p>"
        )
        self.assertEqual(
            html_to_whatsapp(html),
            "Hello *Ana* , _thanks_ ~old~ `x=1`\n\n"
            "Line\nbreak & https://example.com/kb\n"
            "• first\n• second\nBye",
        )
        self.assertEqual(html_to_whatsapp(None), "")
