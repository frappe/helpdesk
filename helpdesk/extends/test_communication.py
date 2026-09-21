# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.api import split_ticket
from helpdesk.patches import backfill_ticket_participants
from helpdesk.test_utils import make_communication, make_ticket


class ParticipantTestCase(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def participants(self, ticket: str) -> set[tuple[str, str]]:
        return {
            (row.email, row.role)
            for row in frappe.get_all(
                "HD Ticket Participant",
                filters={"ticket": ticket},
                fields=["email", "role"],
            )
        }

    def assertRecorded(self, ticket: str, expected: set[tuple[str, str]]) -> None:
        """Asserts presence, not an exact set: HD Ticket writes its own
        Communication on creation, so every ticket also carries a From
        participant for whoever opened it."""
        actual = self.participants(ticket)
        self.assertEqual(expected - actual, set(), f"recorded instead: {actual}")


class TestParticipantCapture(ParticipantTestCase):
    def test_records_the_to_cc_and_from_addresses(self) -> None:
        ticket = make_ticket(subject="Participant capture")

        make_communication(
            ticket.name,
            sender="bob@client.com",
            recipients="support@work.com",
            cc="Kelly Doe <kelly@work.com>, jane@client.com",
        )

        self.assertRecorded(
            ticket.name,
            {
                ("bob@client.com", "From"),
                ("support@work.com", "To"),
                ("kelly@work.com", "Cc"),
                ("jane@client.com", "Cc"),
            },
        )

    def test_the_same_person_on_two_replies_is_recorded_once(self) -> None:
        ticket = make_ticket(subject="Repeat participant")

        make_communication(
            ticket.name, sender="bob@client.com", recipients="support@work.com"
        )
        make_communication(
            ticket.name, sender="bob@client.com", recipients="support@work.com"
        )

        rows = frappe.get_all(
            "HD Ticket Participant",
            filters={"ticket": ticket.name, "email": "support@work.com", "role": "To"},
            pluck="name",
        )
        self.assertEqual(len(rows), 1)

    def test_addresses_are_stored_lowercased(self) -> None:
        """Contact emails are matched exactly, so casing has to be settled
        on the way in rather than at every read."""
        ticket = make_ticket(subject="Mixed case participant")

        make_communication(
            ticket.name, sender="Bob@Client.COM", recipients="Support@Work.Com"
        )

        recorded = self.participants(ticket.name)
        self.assertIn(("bob@client.com", "From"), recorded)
        self.assertIn(("support@work.com", "To"), recorded)
        self.assertNotIn(("Support@Work.Com", "To"), recorded)

    def test_quoted_display_name_containing_a_comma_is_parsed(self) -> None:
        ticket = make_ticket(subject="Quoted participant")

        make_communication(
            ticket.name,
            sender="bob@client.com",
            recipients='"Doe, Kelly" <kelly@work.com>, jane@client.com',
        )

        self.assertRecorded(
            ticket.name, {("kelly@work.com", "To"), ("jane@client.com", "To")}
        )

    def test_group_syntax_does_not_become_a_participant(self) -> None:
        ticket = make_ticket(subject="Group syntax participant")

        make_communication(
            ticket.name,
            sender="bob@client.com",
            recipients="undisclosed-recipients:;",
        )

        recorded = self.participants(ticket.name)
        self.assertRecorded(ticket.name, {("bob@client.com", "From")})
        self.assertEqual([e for e, _ in recorded if "@" not in e], [])
        self.assertNotIn("undisclosed-recipients", [e for e, _ in recorded])

    def test_a_communication_off_a_ticket_records_nothing(self) -> None:
        contact = frappe.get_doc(
            {"doctype": "Contact", "first_name": "OffTicket"}
        ).insert(ignore_permissions=True)

        communication = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "reference_doctype": "Contact",
                "reference_name": contact.name,
                "sent_or_received": "Received",
                "sender": "bob@client.com",
                "recipients": "support@work.com",
                "content": "not about a ticket",
            }
        ).insert(ignore_permissions=True)

        self.assertFalse(
            frappe.db.exists(
                "HD Ticket Participant", {"ticket": communication.reference_name}
            )
        )

    def test_a_capture_failure_does_not_block_the_email(self) -> None:
        """The hook sits on the inbound mail path: losing a participant row
        is recoverable, refusing the customer's email is not."""
        ticket = make_ticket(subject="Capture failure")

        with patch(
            "helpdesk.extends.communication.record_participants",
            side_effect=ValueError("boom"),
        ):
            communication = make_communication(
                ticket.name, sender="bob@client.com", recipients="support@work.com"
            )

        self.assertTrue(frappe.db.exists("Communication", communication.name))
        recorded = self.participants(ticket.name)
        self.assertNotIn(("bob@client.com", "From"), recorded)
        self.assertNotIn(("support@work.com", "To"), recorded)


class TestParticipantLifecycle(ParticipantTestCase):
    def test_a_ticket_with_participants_can_still_be_deleted(self) -> None:
        """Participants hold a Link to the ticket, so without a cascade core
        refuses the delete as still linked."""
        ticket = make_ticket(subject="Deletable ticket")
        make_communication(
            ticket.name, sender="bob@client.com", recipients="support@work.com"
        )
        self.assertTrue(frappe.db.exists("HD Ticket Participant", {"ticket": ticket.name}))

        frappe.delete_doc("HD Ticket", ticket.name, ignore_permissions=True)

        self.assertFalse(frappe.db.exists("HD Ticket", ticket.name))
        self.assertFalse(
            frappe.db.exists("HD Ticket Participant", {"ticket": ticket.name})
        )


class TestParticipantsFollowMovedEmails(ParticipantTestCase):
    """Splitting and merging move communications with raw database writes,
    which fire no document hooks, so the projection has to be resynced."""

    def test_splitting_a_ticket_moves_the_participants(self) -> None:
        ticket = make_ticket(subject="Ticket to split")
        make_communication(
            ticket.name, sender="bob@client.com", recipients="support@work.com"
        )
        moved = make_communication(
            ticket.name, sender="later@client.com", recipients="kelly@work.com"
        )

        new_ticket = split_ticket("Split off", moved.name)

        self.assertRecorded(
            new_ticket, {("later@client.com", "From"), ("kelly@work.com", "To")}
        )
        self.assertNotIn(("kelly@work.com", "To"), self.participants(ticket.name))

    def test_merging_a_ticket_moves_the_participants(self) -> None:
        target = make_ticket(subject="Merge target")
        source = make_ticket(subject="Merge source")
        communication = make_communication(
            source.name, sender="bob@client.com", recipients="kelly@work.com"
        )
        source.db_set("is_merged", 1)
        source.db_set("merged_with", target.name)

        source.reload().redirect_communication_to_merge_target(communication)

        self.assertRecorded(
            target.name, {("bob@client.com", "From"), ("kelly@work.com", "To")}
        )
        self.assertNotIn(("kelly@work.com", "To"), self.participants(source.name))

    def test_a_resync_keeps_a_participant_still_on_another_email(self) -> None:
        """Recomputing rather than moving rows one by one is what stops a
        participant who is also on a remaining email from being dropped."""
        ticket = make_ticket(subject="Shared participant")
        make_communication(
            ticket.name, sender="bob@client.com", recipients="kelly@work.com"
        )
        moved = make_communication(
            ticket.name, sender="bob@client.com", recipients="kelly@work.com"
        )

        split_ticket("Split off shared", moved.name)

        self.assertRecorded(ticket.name, {("kelly@work.com", "To")})


class TestParticipantBackfill(ParticipantTestCase):
    def setUp(self) -> None:
        super().setUp()
        # commit() per batch would end the test transaction and leak rows
        self.addCleanup(patch.stopall)
        patch("frappe.db.commit").start()

    def existing_thread(self) -> str:
        """A thread whose participant rows predate the capture hook."""
        ticket = make_ticket(subject="Backfill thread")
        make_communication(
            ticket.name,
            sender="bob@client.com",
            recipients="Jane Doe <jane@client.com>",
            cc="kelly@work.com",
        )
        frappe.db.delete("HD Ticket Participant", {"ticket": ticket.name})
        return ticket.name

    def test_backfill_records_participants_for_existing_threads(self) -> None:
        ticket = self.existing_thread()

        backfill_ticket_participants.execute()

        self.assertRecorded(
            ticket,
            {
                ("bob@client.com", "From"),
                ("jane@client.com", "To"),
                ("kelly@work.com", "Cc"),
            },
        )

    def test_backfill_can_be_run_again(self) -> None:
        """A large site may not finish in one migrate window, so a rerun has
        to add nothing rather than fail on duplicates."""
        ticket = self.existing_thread()

        backfill_ticket_participants.execute()
        first_pass = self.participants(ticket)
        backfill_ticket_participants.execute()

        self.assertEqual(self.participants(ticket), first_pass)
