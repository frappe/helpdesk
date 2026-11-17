from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.password import remove_encrypted_password

from helpdesk.auth import authenticate
from helpdesk.helpdesk.doctype.hd_ticket.api import get_one
from helpdesk.integrations.whatsapp.api import get_messages
from helpdesk.integrations.whatsapp.test_utils import (
    META_REQUEST,
    make_number,
    make_whatsapp_account,
    make_whatsapp_template,
    mock_meta,
    react_to,
    receive_message,
    requires_whatsapp,
)
from helpdesk.integrations.whatsapp.tests.test_api import as_request
from helpdesk.test_utils import make_contact, make_ticket

EMAIL_ENDPOINT = "frappe.core.doctype.communication.email.make"
GET_MESSAGES = "helpdesk.integrations.whatsapp.api.get_messages"


def send_message(ticket: str, message: str) -> str:
    from whatsapp.whatsapp.api.messages import send_message as send

    to = frappe.db.get_value("WA Message", {"reference_docname": ticket}, "to")
    return send(to, message, reference_doctype="HD Ticket", reference_docname=ticket)


@requires_whatsapp
class TestWhatsAppPortal(IntegrationTestCase):
    """The customer portal's read-only WhatsApp thread."""

    def setUp(self) -> None:
        self.meta = self.enterContext(mock_meta())
        self.customer = make_contact("whatsapp-portal")
        self.number = make_number()
        contact = frappe.get_doc("Contact", self.customer["contact"])
        contact.add_phone(f"+{self.number}", is_primary_mobile_no=1)
        contact.save(ignore_permissions=True)
        self.message = receive_message(
            self.number, "Where is my refund?", make_whatsapp_account()
        )
        self.ticket = self.message.reference_docname

    def test_portal_page_learns_the_ticket_is_whatsapp_not_its_source(self) -> None:
        email_ticket = make_ticket(raised_by=self.customer["user"])
        with self.set_user(self.customer["user"]):
            whatsapp = get_one(self.ticket)
            self.assertTrue(whatsapp["is_whatsapp"])
            self.assertIsNone(whatsapp.get("source"))
            # the portal tells the contact's own bubbles apart by raised_by
            self.assertEqual(whatsapp["raised_by"], self.customer["user"])
            self.assertFalse(get_one(email_ticket.name)["is_whatsapp"])

    def test_block_endpoints_pass_the_thread_but_only_its_contact_reads(self) -> None:
        stranger = make_contact("whatsapp-portal-stranger")["user"]
        # portal sign-ups are Website Users; the gate waves System Users through
        for user in (self.customer["user"], stranger):
            frappe.db.set_value("User", user, "user_type", "Website User")
        send_message(self.ticket, "On it")
        with patch.dict(frappe.conf, {"block_endpoints": 1}):
            with self.set_user(self.customer["user"]):
                self.assertIsNone(call_through_gate(GET_MESSAGES))
                with self.assertRaises(frappe.PermissionError):
                    call_through_gate("frappe.desk.reportview.get")
                with self.assertRaises(frappe.PermissionError):
                    call_through_gate("whatsapp.whatsapp.api.messages.send_message")
                thread = read_thread(self.ticket)["messages"]
                self.assertEqual(thread[0].name, self.message.name)
                # customers see the brand on agent messages, never the agent's email
                self.assertFalse(any("owner" in row for row in thread))
            with self.set_user(stranger):
                self.assertIsNone(call_through_gate(GET_MESSAGES))
                self.assertRaises(frappe.PermissionError, read_thread, self.ticket)
                self.assertRaises(frappe.PermissionError, get_one, self.ticket)

    def test_contact_cannot_email_a_whatsapp_ticket(self) -> None:
        frappe.db.set_value("User", self.customer["user"], "user_type", "Website User")
        status = frappe.db.get_value("HD Ticket", self.ticket, "status")
        with self.set_user(self.customer["user"]):
            ticket = frappe.get_doc("HD Ticket", self.ticket)
            with self.assertRaises(frappe.PermissionError):
                ticket.run_method(
                    "create_communication_via_contact", message="<p>sneaky email</p>"
                )
            # the framework's own email endpoint, open to portal users too
            make = frappe.get_attr(frappe.override_whitelisted_method(EMAIL_ENDPOINT))
            with self.assertRaisesRegex(frappe.ValidationError, "on WhatsApp"):
                make(
                    doctype="HD Ticket",
                    name=self.ticket,
                    content="sneaky",
                    communication_type="Automated Message",
                    send_email=1,
                )
        self.assertFalse(
            frappe.db.exists("Communication", {"reference_name": self.ticket})
        )
        self.assertEqual(
            frappe.db.get_value("HD Ticket", self.ticket, "status"), status
        )

    def test_contact_reads_the_closed_ticket_prompt_with_its_buttons(self) -> None:
        frappe.db.set_value("HD Ticket", self.ticket, "status", "Closed")
        receive_message(self.number, "Hello again", self.message.whatsapp_account)
        with self.set_user(self.customer["user"]):
            thread = read_thread(self.ticket)["messages"]
        self.assertNotIn("buttons", thread[0])
        # the held message stays off the ticket, so the prompt comes last
        self.assertEqual(
            [button["button_text"] for button in thread[-1]["buttons"]],
            ["Create new ticket", "No, thanks"],
        )

    def test_first_response_is_the_first_agent_message_not_a_status_change(
        self,
    ) -> None:
        ticket = frappe.get_doc("HD Ticket", self.ticket)
        ticket.status = "Closed"
        ticket.save(ignore_permissions=True)
        # the prompt is automated, not an agent's reply
        receive_message(self.number, "Hello again", self.message.whatsapp_account)
        with self.set_user(self.customer["user"]):
            closed = get_one(self.ticket)
        self.assertTrue(closed["first_responded_on"])
        self.assertIsNone(closed["first_whatsapp_reply_on"])
        frappe.db.set_value("HD Ticket", self.ticket, "status", "Open")
        reply = frappe.get_doc("WA Message", send_message(self.ticket, "On it"))
        with self.set_user(self.customer["user"]):
            self.assertEqual(
                get_one(self.ticket)["first_whatsapp_reply_on"], reply.creation
            )

    def test_business_number_is_fetched_once_and_cached_for_the_wa_me_link(
        self,
    ) -> None:
        number = {"display_phone_number": "+1 555-010-0199"}
        with patch(META_REQUEST, return_value=number) as lookup:
            with self.set_user(self.customer["user"]):
                for _read in range(2):
                    thread = read_thread(self.ticket)
                    self.assertEqual(thread["business_number"], "15550100199")
        lookup.assert_called_once()
        phone_id = frappe.db.get_value(
            "WA Account", self.message.whatsapp_account, "phone_id"
        )
        self.assertEqual(lookup.call_args.args, ("GET", phone_id))
        self.assertEqual(
            lookup.call_args.kwargs["params"], {"fields": "display_phone_number"}
        )

    def test_business_number_lookup_failure_leaves_the_note_plain(self) -> None:
        with patch(META_REQUEST, side_effect=Exception("Meta is down")):
            with self.set_user(self.customer["user"]):
                self.assertIsNone(read_thread(self.ticket)["business_number"])

    def test_account_without_a_token_skips_the_lookup_and_logs_nothing(self) -> None:
        remove_encrypted_password(
            "WA Account", self.message.whatsapp_account, "access_token"
        )
        frappe.local.message_log = []
        with patch(META_REQUEST) as lookup:
            with self.set_user(self.customer["user"]):
                self.assertIsNone(read_thread(self.ticket)["business_number"])
        lookup.assert_not_called()
        self.assertEqual(frappe.local.message_log, [])

    def test_editing_the_account_drops_its_cached_number(self) -> None:
        number = {"display_phone_number": "+1 555-010-0199"}
        with patch(META_REQUEST, return_value=number) as lookup:
            with self.set_user(self.customer["user"]):
                read_thread(self.ticket)
            account = frappe.get_doc("WA Account", self.message.whatsapp_account)
            account.phone_id = "new-phone-id"
            account.save(ignore_permissions=True)
            with self.set_user(self.customer["user"]):
                read_thread(self.ticket)
        self.assertEqual(lookup.call_count, 2)
        self.assertEqual(lookup.call_args.args, ("GET", "new-phone-id"))

    def test_new_messages_and_failed_sends_ping_the_contact_but_ticks_do_not(
        self,
    ) -> None:
        with patch("frappe.publish_realtime") as publish:
            sent = frappe.get_doc(
                "WA Message", send_message(self.ticket, "First reply")
            )
            receive_message(self.number, "Thanks", self.message.whatsapp_account)
            pinged = customer_pings(publish, self.customer["user"])
            for status in ("delivered", "read"):
                update_status(
                    {"id": sent.message_id, "status": status}, sent.whatsapp_account
                )
            self.assertEqual(customer_pings(publish, self.customer["user"]), pinged)
            update_status(
                {"id": sent.message_id, "status": "failed"}, sent.whatsapp_account
            )
            self.assertEqual(customer_pings(publish, self.customer["user"]), pinged + 1)
            self.assertTrue(
                any(
                    call.args[0] == "whatsapp_message"
                    for call in publish.call_args_list
                )
            )
        self.assertGreaterEqual(pinged, 2)

    def test_contact_reads_quotes_reactions_and_filled_templates(self) -> None:
        from whatsapp.whatsapp.api.messages import send_template

        answer = frappe.get_doc("WA Message", send_message(self.ticket, "On it"))
        account = self.message.whatsapp_account
        react_to(self.number, account, answer.message_id, "👍")
        receive_message(
            self.number, "Thanks", account, context={"id": answer.message_id}
        )
        template = make_whatsapp_template()
        send_template(template, answer.to, "HD Ticket", self.ticket)
        subject = frappe.db.get_value("HD Ticket", self.ticket, "subject")
        with self.set_user(self.customer["user"]):
            thread = read_thread(self.ticket)["messages"]
        # the reaction folds onto the answer instead of taking a row
        self.assertEqual(len(thread), 4)
        self.assertEqual(
            [row["direction"] for row in thread],
            ["Incoming", "Outgoing", "Incoming", "Outgoing"],
        )
        self.assertEqual(
            thread[1]["reactions"], [{"emoji": "👍", "direction": "Incoming"}]
        )
        self.assertEqual(thread[2]["reply_to"], answer.name)
        self.assertEqual(thread[2]["reply_message"], "On it")
        self.assertEqual(thread[3]["template"], f"Hello, your ticket is {subject}")

    def test_contact_reads_only_display_fields_never_send_errors(self) -> None:
        import requests

        secret = "/v23.0/123/messages?access_token=SECRET"
        self.meta.side_effect = requests.ConnectionError(secret)
        failed = send_message(self.ticket, "Lost reply")
        self.meta.side_effect = None
        self.assertEqual(frappe.db.get_value("WA Message", failed, "status"), "Failed")
        # a sender-chosen file name that matches a site file gets no File details
        frappe.get_doc(
            doctype="File", file_name="secret.txt", content=b"x", is_private=1
        ).insert(ignore_permissions=True)
        site_file = frappe.db.get_value("File", {"file_name": "secret.txt"}, "file_url")
        document = {
            "id": "media",
            "mime_type": "application/pdf",
            "filename": site_file,
        }
        receive_message(
            self.number,
            "",
            self.message.whatsapp_account,
            type="document",
            document=document,
        )
        with self.set_user(self.customer["user"]):
            payload = frappe.as_json(read_thread(self.ticket))
            thread = read_thread(self.ticket)["messages"]
        self.assertNotIn("SECRET", payload)
        internals = {"error_message", "to", "from", "message_id", "file_size"}
        self.assertFalse(any(internals & set(row) for row in thread))
        self.assertEqual(thread[1]["status"], "Failed")
        self.assertEqual(thread[2]["media_url"], site_file)
        self.assertNotIn("file_name", thread[2])


def read_thread(ticket: str) -> dict:
    # set_user clears the request form, so set the endpoint per call
    with as_request(GET_MESSAGES):
        return get_messages(ticket)


def update_status(status: dict, account: str) -> None:
    from whatsapp.whatsapp.webhook import _update_message_status

    _update_message_status(status, account)


def customer_pings(publish, user: str) -> int:
    return sum(
        1
        for call in publish.call_args_list
        if call.args[0] == "helpdesk:ticket-update" and call.kwargs.get("user") == user
    )


def call_through_gate(cmd: str) -> None:
    """Run the block_endpoints gate as a request to `cmd` would."""
    with patch.dict(frappe.form_dict, {"cmd": cmd}):
        return authenticate()
