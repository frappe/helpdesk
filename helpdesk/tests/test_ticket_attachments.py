"""A portal reply links only files its sender uploaded for that ticket, never someone else's."""

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import (
    create_contact,
    make_ticket,
    unique_email,
    upload_test_file,
)


class TestTicketAttachments(FrappeTestCase):
    def setUp(self):
        self.owner = self.make_customer_user()
        self.other = self.make_customer_user()
        self.owner_ticket = make_ticket(raised_by=self.owner)
        self.other_ticket = make_ticket(raised_by=self.other)

    def make_customer_user(self):
        email = unique_email("attachment-customer")
        return create_contact(email.split("@")[0], email)["user"]

    def upload_as(self, user, ticket=None):
        with self.set_user(user):
            file_name = upload_test_file("outlook.png")
        if ticket:
            frappe.db.set_value(
                "File",
                file_name,
                {"attached_to_doctype": "HD Ticket", "attached_to_name": ticket},
            )
        return file_name

    def reply_as(self, user, ticket, *file_names):
        with self.set_user(user):
            frappe.get_doc("HD Ticket", ticket).create_communication_via_contact(
                "see attached", attachments=[{"name": name} for name in file_names]
            )

    def attached_to(self, file_name):
        return frappe.db.get_value(
            "File", file_name, ["attached_to_doctype", "attached_to_name"]
        )

    def test_reply_links_own_unattached_and_same_ticket_files(self):
        unattached = self.upload_as(self.other)
        on_ticket = self.upload_as(self.other, self.other_ticket.name)
        self.reply_as(self.other, self.other_ticket.name, unattached, on_ticket)
        for file_name in (unattached, on_ticket):
            self.assertEqual(self.attached_to(file_name)[0], "Communication")

    def test_reply_cannot_take_another_users_file(self):
        stolen = self.upload_as(self.owner, self.owner_ticket.name)
        self.reply_as(self.other, self.other_ticket.name, stolen)
        self.assertEqual(
            self.attached_to(stolen), ("HD Ticket", self.owner_ticket.name)
        )
        self.assertFalse(self.ticket_has_file(self.other_ticket.name, stolen))

    def test_reply_cannot_move_own_file_from_another_ticket(self):
        elsewhere = make_ticket(raised_by=self.other).name
        moved = self.upload_as(self.other, elsewhere)
        self.reply_as(self.other, self.other_ticket.name, moved)
        self.assertEqual(self.attached_to(moved), ("HD Ticket", elsewhere))

    def ticket_has_file(self, ticket, file_name):
        file_url = frappe.db.get_value("File", file_name, "file_url")
        return frappe.db.exists(
            "File",
            {
                "file_url": file_url,
                "attached_to_doctype": "HD Ticket",
                "attached_to_name": ticket,
                "name": ["!=", file_name],
            },
        )
