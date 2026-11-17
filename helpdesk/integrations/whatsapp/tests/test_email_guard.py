import frappe
from frappe.client import set_value
from frappe.core.doctype.communication.email import _make
from frappe.tests import IntegrationTestCase

from helpdesk.api.ticket import bulk_reply
from helpdesk.integrations.whatsapp.test_utils import (
    make_number,
    make_whatsapp_account,
    mock_meta,
    receive_message,
    requires_whatsapp,
)
from helpdesk.overrides.email_account import CustomInboundMail
from helpdesk.test_utils import create_agent, make_ticket

SLA_FIELDS = ["first_responded_on", "last_agent_response", "status"]
EMAIL_ENDPOINT = "frappe.core.doctype.communication.email.make"


@requires_whatsapp
class TestWhatsAppEmailGuard(IntegrationTestCase):
    """Agents cannot email a WhatsApp ticket by any path."""

    def setUp(self) -> None:
        self.enterContext(mock_meta())
        self.ticket = receive_message(
            make_number(), "Where is my order?", make_whatsapp_account()
        ).reference_docname
        self.sla = frappe.db.get_value("HD Ticket", self.ticket, SLA_FIELDS)

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def test_reply_via_agent_refuses_a_whatsapp_ticket(self) -> None:
        ticket = frappe.get_doc("HD Ticket", self.ticket)
        with self.assertRaisesRegex(frappe.ValidationError, "on WhatsApp"):
            ticket.reply_via_agent("<p>Hello by email</p>", to=ticket.raised_by)
        self.assert_untouched()

    def test_framework_email_endpoint_refuses_an_agent(self) -> None:
        make = frappe.get_attr(frappe.override_whitelisted_method(EMAIL_ENDPOINT))
        disguises = [
            {},
            {"communication_type": "Automated Message"},
            {"sent_or_received": "Received"},
            {"communication_medium": "Phone"},
        ]
        for disguise in disguises:
            with (
                self.subTest(**disguise),
                self.assertRaisesRegex(frappe.ValidationError, "on WhatsApp"),
            ):
                make(
                    doctype="HD Ticket",
                    name=self.ticket,
                    content="Hello by email",
                    recipients="customer@example.com",
                    send_email=1,
                    **disguise,
                )
        self.assert_untouched()

    def test_only_a_notification_communication_lands(self) -> None:
        for medium in ["Phone", "Email"]:
            communication = frappe.get_doc(
                doctype="Communication",
                communication_medium=medium,
                sent_or_received="Received",
                reference_doctype="HD Ticket",
                reference_name=self.ticket,
                sender="someone@example.com",
                content="Logged call",
            )
            with (
                self.subTest(medium=medium),
                self.assertRaisesRegex(frappe.ValidationError, "on WhatsApp"),
            ):
                communication.insert(ignore_permissions=True)
        ticket = frappe.get_doc("HD Ticket", self.ticket)
        with self.assertRaisesRegex(frappe.ValidationError, "on WhatsApp"):
            ticket.create_communication_via_contact("From the portal", new_ticket=True)
        self.assert_untouched()
        _make(
            doctype="HD Ticket",
            name=self.ticket,
            content="You were assigned",
            recipients="agent@example.com",
            communication_type="Automated Message",
        )
        self.assertTrue(sent_emails(self.ticket))

    def test_bulk_reply_skips_whatsapp_tickets(self) -> None:
        email_ticket = make_ticket(raised_by="email.guard@example.com").name
        result = bulk_reply(ticket_ids=[email_ticket, self.ticket], message="Hello")
        self.assertEqual(result, {"skipped": [self.ticket]})
        self.assertTrue(sent_emails(email_ticket))
        self.assert_untouched()

    def test_an_agent_cannot_change_the_source(self) -> None:
        email_ticket = make_ticket(raised_by="email.guard@example.com").name
        frappe.set_user(create_agent("email.guard.agent@example.com").name)
        for ticket, source in [(self.ticket, "Email"), (email_ticket, "WhatsApp")]:
            with (
                self.subTest(source=source),
                self.assertRaisesRegex(
                    frappe.ValidationError, "source cannot be changed"
                ),
            ):
                set_value("HD Ticket", ticket, "source", source)
        ticket = frappe.get_doc("HD Ticket", self.ticket)
        with self.assertRaisesRegex(frappe.ValidationError, "on WhatsApp"):
            ticket.reply_via_agent("<p>Hello by email</p>", to="cust@example.com")
        self.assert_untouched()

    def test_received_mail_opens_a_new_email_ticket(self) -> None:
        account = make_inbound_account()
        notification = _make(
            doctype="HD Ticket",
            name=self.ticket,
            content="You were assigned",
            recipients="agent@example.com",
            communication_type="Automated Message",
            send_email=True,
        )["name"]
        message_id = frappe.db.get_value(
            "Email Queue", {"communication": notification}, "message_id"
        )
        triggers = {
            "subject": f"Subject: Re: Order (#{self.ticket})",
            "in_reply_to": f"Subject: Re: You were assigned\nIn-Reply-To: {message_id}",
        }
        for trigger, headers in triggers.items():
            with self.subTest(trigger=trigger):
                communication = CustomInboundMail(raw_mail(headers), account).process()
                ticket = frappe.get_doc("HD Ticket", communication.reference_name)
                self.assertNotEqual(ticket.name, self.ticket)
                self.assertEqual(
                    (ticket.source, ticket.raised_by, ticket.email_account),
                    ("Email", "mail.customer@example.com", account.name),
                )
        self.assertEqual(sent_emails(self.ticket), [notification])

    def assert_untouched(self) -> None:
        self.assertFalse(sent_emails(self.ticket))
        self.assertFalse(
            frappe.db.exists(
                "Email Queue",
                {"reference_doctype": "HD Ticket", "reference_name": self.ticket},
            )
        )
        self.assertEqual(
            frappe.db.get_value("HD Ticket", self.ticket, SLA_FIELDS), self.sla
        )


def make_inbound_account() -> "frappe.model.document.Document":
    return frappe.get_doc(
        doctype="Email Account",
        email_account_name=f"WhatsApp Guard {frappe.generate_hash(length=6)}",
        email_id=f"guard-{frappe.generate_hash(length=6)}@example.com",
        append_to="HD Ticket",
    ).insert(ignore_permissions=True)


def raw_mail(headers: str) -> str:
    return (
        "From: Mail Customer <mail.customer@example.com>\n"
        "To: support@example.com\n"
        f"{headers}\n"
        f"Message-ID: <{frappe.generate_hash()}@example.com>\n"
        "Content-Type: text/plain\n\n"
        "Any update on my order?\n"
    )


def sent_emails(ticket: str) -> list[str]:
    return frappe.get_all(
        "Communication",
        filters={"reference_doctype": "HD Ticket", "reference_name": ticket},
        pluck="name",
    )
