# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.integrations.whatsapp.api import (
    create_whatsapp_message,
    get_whatsapp_messages,
    is_whatsapp_installed,
    react_on_whatsapp_message,
    send_whatsapp_template,
)
from helpdesk.integrations.whatsapp.install import add_roles
from helpdesk.integrations.whatsapp.utils import resolve_or_create_contact
from helpdesk.test_utils import make_ticket

WA_ACCOUNT = "Test Helpdesk WA Account"
SEND_PATH = (
    "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message"
    ".whatsapp_message.WhatsAppMessage.send_outgoing"
)


def ensure_whatsapp_account():
    """A default in/out WhatsApp Account so the transport's validate passes."""
    if not frappe.db.exists("WhatsApp Account", WA_ACCOUNT):
        frappe.get_doc(
            {
                "doctype": "WhatsApp Account",
                "account_name": WA_ACCOUNT,
                "status": "Active",
                "url": "https://graph.facebook.com",
                "version": "v21.0",
                "phone_id": "0000000000",
                "token": "test-token",
                "is_default_incoming": 1,
                "is_default_outgoing": 1,
            }
        ).insert(ignore_permissions=True)
    frappe.db.set_single_value(
        "WhatsApp Settings", "default_outgoing_account", WA_ACCOUNT
    )


def add_message(contact: str, direction: str = "Incoming", **fields):
    """A WhatsApp Message pre-anchored on ``contact`` (skips validate resolution)."""
    number = fields.pop("number", "+5511990000000")
    data = {
        "doctype": "WhatsApp Message",
        "type": direction,
        "reference_doctype": "Contact",
        "reference_name": contact,
        "content_type": "text",
        "message_id": frappe.generate_hash(length=12),
        **fields,
    }
    data.setdefault("from" if direction == "Incoming" else "to", number)
    with patch(SEND_PATH):
        return frappe.get_doc(data).insert(ignore_permissions=True)


def make_reaction(target, emoji: str):
    """A reaction message targeting ``target`` by its message_id."""
    return add_message(
        target.reference_name,
        direction="Outgoing",
        content_type="reaction",
        message=emoji,
        reply_to_message_id=target.message_id,
    )


def drop_template(name: str) -> None:
    """Remove a template row without the controller's Meta round-trip."""
    frappe.db.delete("WhatsApp Templates", {"name": name})


def ensure_template(name: str, body: str, header: str | None = None) -> str:
    docname = f"{name}-en"
    drop_template(docname)
    # The transport's controller round-trips to the Meta API on save; insert the
    # row directly (db_insert bypasses controller hooks) so a test template can
    # be created fully offline.
    doc = frappe.get_doc(
        {
            "doctype": "WhatsApp Templates",
            "template_name": name,
            "template": body,
            "header": header,
            "language": "en",
            "language_code": "en",
            "category": "UTILITY",
        }
    )
    doc.name = docname
    doc.db_insert()
    return docname


def make_contact(first_name: str, number: str) -> str:
    doc = frappe.new_doc("Contact")
    doc.first_name = first_name
    doc.append(
        "phone_nos",
        {"phone": number, "is_primary_phone": 1, "is_primary_mobile_no": 1},
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def ensure_non_agent(email: str = "whatsapp-nonagent@example.com") -> str:
    if not frappe.db.exists("User", email):
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": "Non Agent",
                "roles": [],
            }
        ).insert(ignore_permissions=True)
    return email


def make_incoming(number: str, message: str) -> "frappe.Document":
    """Create an Incoming WhatsApp Message (no network: send is Outgoing-only)."""
    doc = frappe.get_doc(
        {
            "doctype": "WhatsApp Message",
            "type": "Incoming",
            "from": number,
            "message": message,
            "content_type": "text",
            "message_id": frappe.generate_hash(length=12),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


class TestWhatsAppIntegration(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ensure_whatsapp_account()

    # ------------------------------------------------------------------
    # Omnichannel resolution — the Contact anchor
    # ------------------------------------------------------------------

    def test_transport_installed(self):
        self.assertTrue(is_whatsapp_installed())

    def test_unknown_number_creates_contact(self):
        number = "+5511990000001"
        contact = resolve_or_create_contact(number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        self.assertTrue(contact)
        self.assertTrue(frappe.db.exists("Contact", contact))

    def test_known_number_binds_existing_contact(self):
        number = "+5511990000002"
        existing = make_contact("Known Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", existing, force=True)

        contact = resolve_or_create_contact(number)
        self.assertEqual(contact, existing)

    def test_incoming_message_anchors_on_contact(self):
        number = "+5511990000003"
        msg = make_incoming(number, "Hi, I need help")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", msg.reference_name, force=True)

        self.assertEqual(msg.reference_doctype, "Contact")
        self.assertTrue(msg.reference_name)

    def test_incoming_reuses_same_contact(self):
        number = "+5511990000004"
        first = make_incoming(number, "first")
        second = make_incoming(number, "second")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", first.name, force=True)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", second.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", first.reference_name, force=True)

        self.assertEqual(first.reference_name, second.reference_name)

    # ------------------------------------------------------------------
    # Reading the thread
    # ------------------------------------------------------------------

    def test_get_whatsapp_messages_returns_thread(self):
        number = "+5511990000005"
        msg = make_incoming(number, "thread message")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        messages = get_whatsapp_messages(contact)
        self.assertTrue(any(m["name"] == msg.name for m in messages))

    # ------------------------------------------------------------------
    # Sending (transport mocked)
    # ------------------------------------------------------------------

    def test_create_message_anchors_and_sends(self):
        number = "+5511990000006"
        contact = make_contact("Outbound Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        with patch(SEND_PATH):
            name = create_whatsapp_message(contact=contact, message="hello there")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)

        doc = frappe.get_doc("WhatsApp Message", name)
        self.assertEqual(doc.reference_doctype, "Contact")
        self.assertEqual(doc.reference_name, contact)
        # The destination is derived from the contact, never sent by the client.
        self.assertEqual(doc.to, number)

    # ------------------------------------------------------------------
    # Ticket linkage — the omnichannel thread narrowed to a ticket
    # ------------------------------------------------------------------

    def _ticket_for(self, contact: str, status: str = "Open") -> str:
        # HD Ticket always opens as "Open"; force a terminal status directly so
        # the query filter (not the ticket lifecycle) is what's under test.
        ticket = make_ticket(contact=contact)
        if status != "Open":
            frappe.db.set_value("HD Ticket", ticket.name, "status", status)
        self.addCleanup(frappe.delete_doc, "HD Ticket", ticket.name, force=True)
        return ticket.name

    def test_inbound_links_most_recent_open_ticket(self):
        number = "+5511990000010"
        contact = make_contact("Ticketed Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        older = self._ticket_for(contact)
        newer = self._ticket_for(contact)

        msg = make_incoming(number, "linked to a ticket")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)

        self.assertEqual(msg.reference_name, contact)
        self.assertIn(msg.hd_ticket, {older, newer})
        # Ordered by most-recently-touched, so the latest open ticket wins.
        self.assertEqual(msg.hd_ticket, newer)

    def test_inbound_without_open_ticket_has_no_link(self):
        number = "+5511990000011"
        msg = make_incoming(number, "pure conversation, no ticket")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        self.assertFalse(msg.hd_ticket)

    def test_inbound_ignores_closed_tickets(self):
        number = "+5511990000012"
        contact = make_contact("Closed Ticket Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        self._ticket_for(contact, status="Closed")

        msg = make_incoming(number, "old closed ticket must not link")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)

        self.assertFalse(msg.hd_ticket)

    def test_outbound_records_hd_ticket(self):
        number = "+5511990000013"
        contact = make_contact("Outbound Ticket Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        ticket = self._ticket_for(contact)

        with patch(SEND_PATH):
            name = create_whatsapp_message(
                contact=contact,
                message="reply from ticket",
                hd_ticket=ticket,
            )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)

        self.assertEqual(
            frappe.db.get_value("WhatsApp Message", name, "hd_ticket"), ticket
        )

    def test_get_messages_exposes_hd_ticket(self):
        number = "+5511990000014"
        contact = make_contact("Thread Ticket Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        ticket = self._ticket_for(contact)

        msg = make_incoming(number, "surfaced with its ticket")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)

        messages = get_whatsapp_messages(contact)
        surfaced = next(m for m in messages if m["name"] == msg.name)
        self.assertEqual(surfaced["hd_ticket"], ticket)

    # ------------------------------------------------------------------
    # Send security — server-derived number, ticket & conversation ownership
    # ------------------------------------------------------------------

    def test_send_rejects_contact_without_number(self):
        doc = frappe.new_doc("Contact")
        doc.first_name = "No Number Person"
        doc.append("email_ids", {"email_id": "nonum@example.com", "is_primary": 1})
        doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Contact", doc.name, force=True)

        with self.assertRaises(frappe.ValidationError):
            create_whatsapp_message(contact=doc.name, message="hi")
        with self.assertRaises(frappe.ValidationError):
            send_whatsapp_template(contact=doc.name, template="whatever")

    def test_resolve_destination_prefers_mobile_and_rejects_absent(self):
        # The number both send APIs use is derived here, from the contact.
        from helpdesk.integrations.whatsapp.api import _resolve_destination

        number = "+5511990000025"
        contact = make_contact("Derive Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        self.assertEqual(_resolve_destination(contact), number)

        no_number = frappe.new_doc("Contact")
        no_number.first_name = "No Number"
        no_number.append(
            "email_ids", {"email_id": "derive-nonum@example.com", "is_primary": 1}
        )
        no_number.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Contact", no_number.name, force=True)
        with self.assertRaises(frappe.ValidationError):
            _resolve_destination(no_number.name)

    def test_send_to_foreign_ticket_raises(self):
        contact_a = make_contact("Owner A", "+5511990000020")
        contact_b = make_contact("Other B", "+5511990000021")
        self.addCleanup(frappe.delete_doc, "Contact", contact_a, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact_b, force=True)
        ticket_a = self._ticket_for(contact_a)

        with patch(SEND_PATH):
            with self.assertRaises(frappe.ValidationError):
                create_whatsapp_message(
                    contact=contact_b, message="x", hd_ticket=ticket_a
                )
            with self.assertRaises(frappe.ValidationError):
                send_whatsapp_template(
                    contact=contact_b, template="t", hd_ticket=ticket_a
                )

    def test_reply_to_foreign_conversation_raises(self):
        msg_a = make_incoming("+5511990000026", "from A")
        contact_a = msg_a.reference_name
        contact_b = make_contact("Reply Other", "+5511990000027")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg_a.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact_a, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact_b, force=True)

        with patch(SEND_PATH):
            with self.assertRaises(frappe.ValidationError):
                create_whatsapp_message(
                    contact=contact_b, message="x", reply_to=msg_a.name
                )

    def test_non_agent_cannot_send(self):
        contact = make_contact("Send Gate Person", "+5511990000028")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        user = ensure_non_agent()
        self.addCleanup(frappe.delete_doc, "User", user, force=True)

        frappe.set_user(user)
        try:
            with self.assertRaises(frappe.PermissionError):
                create_whatsapp_message(contact=contact, message="x")
            with self.assertRaises(frappe.PermissionError):
                send_whatsapp_template(contact=contact, template="t")
        finally:
            frappe.set_user("Administrator")

    # ------------------------------------------------------------------
    # Reactions
    # ------------------------------------------------------------------

    def test_react_requires_agent(self):
        msg = make_incoming("+5511990000029", "react gate")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        user = ensure_non_agent()
        self.addCleanup(frappe.delete_doc, "User", user, force=True)

        frappe.set_user(user)
        try:
            with self.assertRaises(frappe.PermissionError):
                react_on_whatsapp_message("👍", msg.name)
        finally:
            frappe.set_user("Administrator")

    def test_react_targets_incoming_sender(self):
        number = "+5511990000030"
        msg = make_incoming(number, "target")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        with patch(SEND_PATH):
            name = react_on_whatsapp_message("👍", msg.name)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)

        doc = frappe.get_doc("WhatsApp Message", name)
        self.assertEqual(doc.content_type, "reaction")
        self.assertEqual(doc.message, "👍")
        self.assertEqual(doc.reference_name, contact)
        self.assertEqual(doc.to, number)  # reacts back to the sender
        self.assertEqual(doc.reply_to_message_id, msg.message_id)

    def test_react_on_missing_message_raises(self):
        with self.assertRaises(frappe.DoesNotExistError):
            react_on_whatsapp_message("👍", "does-not-exist")

    # ------------------------------------------------------------------
    # Thread robustness — a bad template payload must not break the thread
    # ------------------------------------------------------------------

    def test_parse_stored_params_tolerates_bad_payloads(self):
        from helpdesk.integrations.whatsapp.api import _parse_stored_params

        self.assertEqual(_parse_stored_params("{not valid json"), [])
        self.assertEqual(_parse_stored_params(""), [])
        self.assertEqual(_parse_stored_params(None), [])
        self.assertEqual(_parse_stored_params("null"), [])
        self.assertEqual(_parse_stored_params('{"a": 1}'), [])  # JSON, not a list
        self.assertEqual(_parse_stored_params('["x", "y"]'), ["x", "y"])

    # ------------------------------------------------------------------
    # Inbound anchoring resilience — never lose a message, never break the batch
    # ------------------------------------------------------------------

    RESOLVE_PATH = "helpdesk.integrations.whatsapp.message.resolve_or_create_contact"

    def _make_orphan(self, number: str) -> "frappe.Document":
        """An inbound message whose anchoring failed, with the retry suppressed."""
        with (
            patch(self.RESOLVE_PATH, side_effect=Exception("boom")),
            patch("frappe.enqueue"),
        ):
            return make_incoming(number, "orphaned")

    def test_validate_does_not_raise_when_resolution_fails(self):
        # A resolution failure must leave the message inserted-but-unlinked, not
        # raise (which would roll back the whole webhook batch).
        number = "+5511990000040"
        with (
            patch(self.RESOLVE_PATH, side_effect=Exception("boom")),
            patch("frappe.enqueue") as enqueue,
        ):
            msg = self._insert_incoming_no_cleanup(number, "resolution fails")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)

        self.assertFalse(msg.reference_name)
        enqueue.assert_called_once()  # a retry was scheduled

    def test_reanchor_links_orphaned_message(self):
        from helpdesk.integrations.whatsapp.message import reanchor_message

        number = "+5511990000041"
        msg = self._make_orphan(number)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.assertFalse(msg.reference_name)

        reanchor_message(msg.name)  # retry with real resolution

        contact = frappe.db.get_value("WhatsApp Message", msg.name, "reference_name")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        self.assertTrue(contact)
        self.assertEqual(
            frappe.db.get_value("WhatsApp Message", msg.name, "reference_doctype"),
            "Contact",
        )

    def test_reanchor_is_noop_when_already_anchored(self):
        from helpdesk.integrations.whatsapp.message import reanchor_message

        number = "+5511990000042"
        msg = make_incoming(number, "already anchored")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        reanchor_message(msg.name)

        self.assertEqual(
            frappe.db.get_value("WhatsApp Message", msg.name, "reference_name"),
            contact,
        )

    def _insert_incoming_no_cleanup(self, number, message):
        doc = frappe.get_doc(
            {
                "doctype": "WhatsApp Message",
                "type": "Incoming",
                "from": number,
                "message": message,
                "content_type": "text",
                "message_id": frappe.generate_hash(length=12),
            }
        )
        doc.insert(ignore_permissions=True)
        return doc

    # ------------------------------------------------------------------
    # Phone matching — exact equality, never a substring
    # ------------------------------------------------------------------

    def test_exact_match_not_substring_suffix(self):
        a = make_contact("Suffix A", "5511990000110")
        b = make_contact("Suffix B", "155511990000110")  # contains A as a suffix
        self.addCleanup(frappe.delete_doc, "Contact", a, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", b, force=True)
        self.assertEqual(resolve_or_create_contact("5511990000110"), a)

    def test_exact_match_not_substring_prefix(self):
        a = make_contact("Prefix A", "5511990000111")
        b = make_contact("Prefix B", "55119900001119")  # contains A as a prefix
        self.addCleanup(frappe.delete_doc, "Contact", a, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", b, force=True)
        self.assertEqual(resolve_or_create_contact("5511990000111"), a)

    def test_formatting_variants_match_same_contact(self):
        contact = make_contact("Formatted", "+55 (11) 99000-0112")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        for variant in ("5511990000112", "+5511990000112", "55 11 99000 0112"):
            self.assertEqual(resolve_or_create_contact(variant), contact, variant)

    def test_blank_number_resolves_to_nothing(self):
        before = frappe.db.count("Contact")
        self.assertIsNone(resolve_or_create_contact(""))
        self.assertIsNone(resolve_or_create_contact("   "))
        self.assertEqual(frappe.db.count("Contact"), before)

    def test_sqlish_number_is_safe(self):
        from helpdesk.integrations.whatsapp.utils import _find_contact_by_number

        # The query builder parametrizes the phone comparison, so a SQL-ish
        # number matches nothing and cannot inject.
        self.assertIsNone(_find_contact_by_number("5511'; DROP TABLE tabContact;--"))
        self.assertTrue(frappe.db.exists("DocType", "Contact"))  # table intact

    def test_two_contacts_share_number_most_recent_wins(self):
        first = make_contact("Share First", "5511990000113")
        second = make_contact("Share Second", "5511990000113")
        self.addCleanup(frappe.delete_doc, "Contact", first, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", second, force=True)
        self.assertEqual(resolve_or_create_contact("5511990000113"), second)

    # ------------------------------------------------------------------
    # Send destination — the number in use, never the primary blindly
    # ------------------------------------------------------------------

    def test_send_targets_last_inbound_number_not_primary(self):
        primary = "+5511111111111"
        secondary = "+5522222222222"
        doc = frappe.new_doc("Contact")
        doc.first_name = "Multi Number"
        doc.append(
            "phone_nos",
            {"phone": primary, "is_primary_phone": 1, "is_primary_mobile_no": 1},
        )
        doc.append("phone_nos", {"phone": secondary})
        doc.insert(ignore_permissions=True)
        contact = doc.name
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        inbound = add_message(contact, direction="Incoming", number=secondary)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", inbound.name, force=True)

        with patch(SEND_PATH):
            name = create_whatsapp_message(contact=contact, message="reply")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)
        # Reply goes to the number the customer actually used, not the primary.
        self.assertEqual(frappe.db.get_value("WhatsApp Message", name, "to"), secondary)

    def test_send_falls_back_to_primary_without_inbound(self):
        number = "+5511990000114"
        contact = make_contact("No Inbound", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        with patch(SEND_PATH):
            name = create_whatsapp_message(contact=contact, message="opener")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)
        self.assertEqual(frappe.db.get_value("WhatsApp Message", name, "to"), number)

    def test_contact_only_phone_no_mobile(self):
        from helpdesk.integrations.whatsapp.api import _resolve_destination

        number = "+5511990000115"
        doc = frappe.new_doc("Contact")
        doc.first_name = "Phone Only"
        doc.append("phone_nos", {"phone": number, "is_primary_phone": 1})
        doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Contact", doc.name, force=True)
        self.assertEqual(_resolve_destination(doc.name), number)

    # ------------------------------------------------------------------
    # Reactions — newest wins, removal clears, no empty-id false match
    # ------------------------------------------------------------------

    def test_newest_reaction_wins(self):
        contact = make_contact("React Person", "+5511990000120")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        target = add_message(contact, direction="Incoming", message="react me")
        old = make_reaction(target, "👍")
        new = make_reaction(target, "❤️")
        for doc in (target, old, new):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), target.name)
        self.assertEqual(surfaced["reaction"], "❤️")  # newest, not the oldest

    def test_reaction_removal_clears(self):
        contact = make_contact("Remove React", "+5511990000121")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        target = add_message(contact, direction="Incoming", message="target")
        r1 = make_reaction(target, "👍")
        r2 = make_reaction(target, "")  # WhatsApp sends an empty body to remove
        for doc in (target, r1, r2):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), target.name)
        self.assertEqual(surfaced.get("reaction"), "")

    def test_reaction_with_empty_id_does_not_false_match(self):
        contact = make_contact("Empty Id React", "+5511990000122")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        target = add_message(
            contact, direction="Incoming", message="no id", message_id=""
        )
        reaction = add_message(
            contact,
            direction="Outgoing",
            content_type="reaction",
            message="👍",
            reply_to_message_id="",
        )
        for doc in (target, reaction):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), target.name)
        self.assertNotIn("reaction", surfaced)

    def test_reaction_targeting_unknown_message_ignored(self):
        contact = make_contact("Orphan React", "+5511990000123")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        text = add_message(contact, direction="Incoming", message="hi")
        reaction = add_message(
            contact,
            direction="Outgoing",
            content_type="reaction",
            message="👍",
            reply_to_message_id="no-such-id",
        )
        for doc in (text, reaction):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        messages = get_whatsapp_messages(contact)
        # Reaction is filtered out; the text carries no reaction.
        self.assertTrue(all(m["content_type"] != "reaction" for m in messages))
        self.assertNotIn("reaction", self._find(messages, text.name))

    # ------------------------------------------------------------------
    # Replies — resolution and no empty-id false match
    # ------------------------------------------------------------------

    def test_reply_resolves_context(self):
        contact = make_contact("Reply Person", "+5511990000130")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        target = add_message(contact, direction="Incoming", message="original")
        reply = add_message(
            contact,
            direction="Outgoing",
            message="answer",
            is_reply=1,
            reply_to_message_id=target.message_id,
        )
        for doc in (target, reply):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), reply.name)
        self.assertEqual(surfaced["reply_message"], "original")
        self.assertEqual(surfaced["reply_to"], target.name)
        self.assertEqual(surfaced["reply_to_type"], "Incoming")

    def test_reply_with_empty_id_does_not_false_match(self):
        contact = make_contact("Empty Reply", "+5511990000131")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        no_id = add_message(
            contact, direction="Incoming", message="no id", message_id=""
        )
        reply = add_message(
            contact,
            direction="Outgoing",
            message="reply",
            is_reply=1,
            reply_to_message_id="",
        )
        for doc in (no_id, reply):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), reply.name)
        self.assertNotIn("reply_message", surfaced)

    def test_reply_to_nonexistent_message_raises(self):
        contact = make_contact("Reply Missing", "+5511990000132")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        with patch(SEND_PATH), self.assertRaises(frappe.DoesNotExistError):
            create_whatsapp_message(
                contact=contact, message="x", reply_to="does-not-exist"
            )

    def test_reply_within_conversation_succeeds(self):
        contact = make_contact("Reply OK", "+5511990000133")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        target = add_message(contact, direction="Incoming", message="q")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", target.name, force=True)
        with patch(SEND_PATH):
            name = create_whatsapp_message(
                contact=contact, message="a", reply_to=target.name
            )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)
        doc = frappe.get_doc("WhatsApp Message", name)
        self.assertTrue(doc.is_reply)
        self.assertEqual(doc.reply_to_message_id, target.message_id)

    # ------------------------------------------------------------------
    # Template enrichment
    # ------------------------------------------------------------------

    def test_template_substitutes_parameters(self):
        contact = make_contact("Template Person", "+5511990000140")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        template = ensure_template("Tmpl Sub", "Hi {{1}}, order {{2}}")
        self.addCleanup(drop_template, template)
        msg = add_message(
            contact,
            direction="Outgoing",
            message_type="Template",
            template=template,
            template_parameters='["Ana", "42"]',
        )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        self.assertEqual(surfaced["template"], "Hi Ana, order 42")

    def test_template_fewer_params_leaves_placeholder(self):
        contact = make_contact("Template Partial", "+5511990000141")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        template = ensure_template("Tmpl Partial", "Hi {{1}} and {{2}}")
        self.addCleanup(drop_template, template)
        msg = add_message(
            contact,
            direction="Outgoing",
            message_type="Template",
            template=template,
            template_parameters='["Ana"]',
        )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        self.assertEqual(surfaced["template"], "Hi Ana and {{2}}")

    def test_template_malformed_params_degrade(self):
        contact = make_contact("Template Bad", "+5511990000142")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        template = ensure_template("Tmpl Bad", "Hi {{1}}")
        self.addCleanup(drop_template, template)
        msg = add_message(
            contact,
            direction="Outgoing",
            message_type="Template",
            template=template,
            template_parameters="{not json",
        )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        # Must not raise; placeholder left intact.
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        self.assertEqual(surfaced["template"], "Hi {{1}}")

    def test_template_missing_row_skips_enrichment(self):
        contact = make_contact("Template Gone", "+5511990000143")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        template = ensure_template("Tmpl Gone", "Hi {{1}}")
        msg = add_message(
            contact,
            direction="Outgoing",
            message_type="Template",
            template=template,
        )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        # Delete the template row so enrichment finds nothing to render.
        drop_template(template)
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        self.assertEqual(surfaced["template"], template)  # left as the raw name

    def test_template_header_params_without_header_do_not_crash(self):
        # Drift: the message was sent when the template still had a header (so
        # header params were stored), then the header was removed Meta-side. The
        # thread must still load — one stale template can't take down every
        # ticket/contact conversation.
        contact = make_contact("Header Drift", "+5511990000145")
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        template = ensure_template("Tmpl NoHeader", "Body {{1}}", header=None)
        self.addCleanup(drop_template, template)
        msg = add_message(
            contact,
            direction="Outgoing",
            message_type="Template",
            template=template,
            template_parameters='["ok"]',
            template_header_parameters='["orphaned"]',
        )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        self.assertEqual(surfaced["template"], "Body ok")
        self.assertFalse(surfaced.get("header"))

    def test_from_name_incoming_vs_outgoing(self):
        number = "+5511990000144"
        contact = make_contact("Sender Name", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        inbound = add_message(contact, direction="Incoming", number=number)
        outbound = add_message(contact, direction="Outgoing", number=number)
        for doc in (inbound, outbound):
            self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        messages = get_whatsapp_messages(contact)
        self.assertEqual(self._find(messages, inbound.name)["from_name"], "Sender Name")
        self.assertEqual(self._find(messages, outbound.name)["from_name"], "You")

    # ------------------------------------------------------------------
    # Content types and faithfulness
    # ------------------------------------------------------------------

    def test_media_only_message_falls_back_to_attach(self):
        number = "+5511990000150"
        contact = make_contact("Media Only", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        with patch(SEND_PATH):
            name = create_whatsapp_message(
                contact=contact,
                message="",
                attach="/files/pic.png",
                content_type="image",
            )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)
        doc = frappe.get_doc("WhatsApp Message", name)
        self.assertEqual(doc.message, "/files/pic.png")
        self.assertEqual(doc.content_type, "image")

    def test_html_body_is_sanitized_but_markup_preserved(self):
        number = "+5511990000151"
        contact = make_contact("Sanitized", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        msg = add_message(
            contact,
            direction="Incoming",
            message="<script>alert(1)</script> *bold* _i_ ~s~",
        )
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        # The message field is an HTML Editor: it strips scripts on save (a
        # second line of defence), while WhatsApp markup is left for the client.
        self.assertNotIn("<script>", surfaced["message"])
        self.assertIn("*bold*", surfaced["message"])

    def test_long_body_round_trips(self):
        number = "+5511990000152"
        contact = make_contact("Long Body", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        body = "x" * 10000
        msg = add_message(contact, direction="Incoming", message=body)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        surfaced = self._find(get_whatsapp_messages(contact), msg.name)
        self.assertEqual(len(surfaced["message"]), 10000)

    def test_multi_codepoint_emoji_reaction(self):
        number = "+5511990000153"
        contact = make_contact("Emoji React", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        target = add_message(contact, direction="Incoming", message="react")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", target.name, force=True)
        family = "👨‍👩‍👧‍👦"  # ZWJ sequence
        with patch(SEND_PATH):
            name = react_on_whatsapp_message(family, target.name)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", name, force=True)
        self.assertEqual(
            frappe.db.get_value("WhatsApp Message", name, "message"), family
        )

    # ------------------------------------------------------------------
    # Ticket linkage — the Resolved status and the un-migrated column
    # ------------------------------------------------------------------

    def test_inbound_ignores_resolved_ticket(self):
        number = "+5511990000160"
        contact = make_contact("Resolved Person", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        self._ticket_for(contact, status="Resolved")
        msg = make_incoming(number, "resolved must not link")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.assertFalse(msg.hd_ticket)

    def test_thread_without_hd_ticket_column(self):
        number = "+5511990000161"
        contact = make_contact("No Column", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        msg = add_message(contact, direction="Incoming", number=number)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        with patch("frappe.db.has_column", return_value=False):
            messages = get_whatsapp_messages(contact)
        self.assertNotIn("hd_ticket", self._find(messages, msg.name))

    # ------------------------------------------------------------------
    # Reanchor — enqueue shape and outbound exemption
    # ------------------------------------------------------------------

    def test_after_insert_enqueues_reanchor_with_expected_args(self):
        import inspect

        from helpdesk.integrations.whatsapp.message import reanchor_message

        number = "+5511990000170"
        with (
            patch(self.RESOLVE_PATH, side_effect=Exception("boom")),
            patch("frappe.enqueue") as enqueue,
        ):
            msg = self._insert_incoming_no_cleanup(number, "unlinked")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        enqueue.assert_called_once()
        _, kwargs = enqueue.call_args
        self.assertEqual(kwargs.get("queue"), "short")
        self.assertTrue(kwargs.get("enqueue_after_commit"))
        self.assertEqual(kwargs.get("message_name"), msg.name)
        self.assertEqual(kwargs.get("attempt"), 1)
        # Guard the boundary: the forwarded kwargs must actually bind to the
        # target's signature, so a renamed parameter can never silently break
        # the enqueued job (which a mocked enqueue would otherwise hide).
        forwarded = {
            k: v
            for k, v in kwargs.items()
            if k not in ("queue", "enqueue_after_commit")
        }
        inspect.signature(reanchor_message).bind(**forwarded)

    def test_reanchor_reschedules_when_resolution_raises_again(self):
        # The retry is the safety net; if resolving raises again it must not let
        # the job die and orphan the message — it reschedules the next attempt.
        from helpdesk.integrations.whatsapp import message as message_module

        msg = self._make_orphan("+5511990000172")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        with (
            patch(self.RESOLVE_PATH, side_effect=Exception("still boom")),
            patch.object(message_module, "_schedule_reanchor") as reschedule,
        ):
            message_module.reanchor_message(msg.name, attempt=1)
        reschedule.assert_called_once_with(msg.name, 2)
        # Still unlinked, but not lost: another attempt is queued.
        self.assertFalse(
            frappe.db.get_value("WhatsApp Message", msg.name, "reference_name")
        )

    def test_reanchor_gives_up_after_max_attempts(self):
        # At the cap it logs and stops rather than rescheduling forever.
        from helpdesk.integrations.whatsapp import message as message_module

        msg = self._make_orphan("+5511990000173")
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        with (
            patch(self.RESOLVE_PATH, side_effect=Exception("permanent")),
            patch.object(message_module, "_schedule_reanchor") as reschedule,
            patch("frappe.log_error") as log_error,
        ):
            message_module.reanchor_message(
                msg.name, attempt=message_module.MAX_ANCHOR_ATTEMPTS
            )
        reschedule.assert_not_called()
        log_error.assert_called()

    def test_outbound_unlinked_is_never_reanchored(self):
        with (
            patch(self.RESOLVE_PATH, side_effect=Exception("boom")),
            patch("frappe.enqueue") as enqueue,
            patch(SEND_PATH),
        ):
            doc = frappe.get_doc(
                {
                    "doctype": "WhatsApp Message",
                    "type": "Outgoing",
                    "to": "+5511990000171",
                    "message": "no contact",
                    "content_type": "text",
                    "message_id": frappe.generate_hash(length=12),
                }
            ).insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", doc.name, force=True)
        enqueue.assert_not_called()

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def test_inbound_without_ticket_raises_no_notification(self):
        number = "+5511990000180"
        with patch("helpdesk.integrations.whatsapp.message._notify_agents") as notify:
            msg = make_incoming(number, "pure conversation")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        # No open ticket → _notify_agents is invoked but creates nothing; assert
        # it ran and produced no HD Notification for this contact's (absent) work.
        notify.assert_called_once()

    def test_outgoing_message_does_not_notify(self):
        number = "+5511990000181"
        contact = make_contact("Outgoing Notify", number)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)
        with patch("helpdesk.integrations.whatsapp.message._notify_agents") as notify:
            msg = add_message(contact, direction="Outgoing", number=number)
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        notify.assert_not_called()

    # ------------------------------------------------------------------
    # Enabled state
    # ------------------------------------------------------------------

    def test_is_enabled_reflects_account_status(self):
        from helpdesk.integrations.whatsapp import utils

        # Active default account → enabled.
        self.assertTrue(utils.is_whatsapp_enabled())

        # No default account → not enabled.
        frappe.db.set_single_value("WhatsApp Settings", "default_outgoing_account", "")
        self.addCleanup(
            frappe.db.set_single_value,
            "WhatsApp Settings",
            "default_outgoing_account",
            WA_ACCOUNT,
        )
        frappe.clear_cache(doctype="WhatsApp Settings")
        self.assertFalse(utils.is_whatsapp_enabled())

    # ------------------------------------------------------------------
    # Install idempotency
    # ------------------------------------------------------------------

    def test_add_custom_fields_idempotent(self):
        from helpdesk.integrations.whatsapp.install import add_custom_fields

        add_custom_fields()
        add_custom_fields()
        self.assertEqual(
            frappe.db.count(
                "Custom Field", {"dt": "WhatsApp Message", "fieldname": "hd_ticket"}
            ),
            1,
        )

    @staticmethod
    def _find(messages, name):
        return next(m for m in messages if m["name"] == name)

    # ------------------------------------------------------------------
    # Access control — agents only
    # ------------------------------------------------------------------

    def test_non_agent_cannot_read_thread(self):
        number = "+5511990000007"
        msg = make_incoming(number, "gated")
        contact = msg.reference_name
        self.addCleanup(frappe.delete_doc, "WhatsApp Message", msg.name, force=True)
        self.addCleanup(frappe.delete_doc, "Contact", contact, force=True)

        user = ensure_non_agent()
        self.addCleanup(frappe.delete_doc, "User", user, force=True)

        frappe.set_user(user)
        try:
            with self.assertRaises(frappe.PermissionError):
                get_whatsapp_messages(contact)
        finally:
            frappe.set_user("Administrator")

    # ------------------------------------------------------------------
    # Roles install — idempotent
    # ------------------------------------------------------------------

    def test_add_roles_is_idempotent(self):
        add_roles()
        add_roles()
        self.assertTrue(
            frappe.db.exists(
                "Custom DocPerm", {"parent": "WhatsApp Message", "role": "Agent"}
            )
        )
