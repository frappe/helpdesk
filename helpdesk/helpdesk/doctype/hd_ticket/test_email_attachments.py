import frappe
from frappe.core.doctype.file.utils import find_file_by_url
from frappe.tests import IntegrationTestCase

from helpdesk.extends.file import strip_email_file_ids
from helpdesk.patches.mirror_email_attachments_to_tickets import (
    execute as mirror_existing,
)
from helpdesk.test_utils import create_contact, make_agent, make_customer_ticket

CUSTOMER = "attachments.customer@example.com"
OTHER_CUSTOMER = "attachments.other@example.com"
AGENT = "attachments.agent@example.com"


class TestEmailAttachments(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        create_contact("Attachment Customer", CUSTOMER)
        create_contact("Other Customer", OTHER_CUSTOMER)
        make_agent(AGENT)
        self.ticket = make_customer_ticket(self, raised_by=CUSTOMER)

    def tearDown(self):
        frappe.set_user("Administrator")

    def email(self, sent_or_received="Received"):
        email = frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Email",
                "sent_or_received": sent_or_received,
                "sender": CUSTOMER,
                "subject": self.ticket.subject,
                "content": "<p>See attachment</p>",
                "reference_doctype": "HD Ticket",
                "reference_name": self.ticket.name,
            }
        ).insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Communication", email.name, force=True)
        return email

    def attach(self, doctype, name, file_name="invoice.txt"):
        file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "content": frappe.generate_hash(),
                "is_private": 1,
                "attached_to_doctype": doctype,
                "attached_to_name": name,
            }
        ).insert(ignore_permissions=True)
        self.addCleanup(self.delete_rows, file.file_url)
        return file

    def delete_rows(self, file_url):
        frappe.db.delete("File", {"file_url": file_url})

    def readable_by(self, user, file_url, fid=None):
        frappe.set_user(user)
        try:
            return bool(find_file_by_url(file_url, name=fid))
        finally:
            frappe.set_user("Administrator")

    def ticket_rows(self, file_url):
        return frappe.db.count(
            "File",
            {
                "file_url": file_url,
                "attached_to_doctype": "HD Ticket",
                "attached_to_name": self.ticket.name,
            },
        )

    def test_customer_reads_attachment_of_received_email(self):
        file = self.attach("Communication", self.email().name)
        self.assertEqual(self.ticket_rows(file.file_url), 1)
        self.assertTrue(self.readable_by(CUSTOMER, file.file_url))
        self.assertTrue(self.readable_by(AGENT, file.file_url))

    def test_customer_reads_attachment_of_sent_email(self):
        file = self.attach("Communication", self.email("Sent").name)
        self.assertTrue(self.readable_by(CUSTOMER, file.file_url))

    def test_other_customer_cannot_read_attachment(self):
        file = self.attach("Communication", self.email().name)
        self.assertFalse(self.readable_by(OTHER_CUSTOMER, file.file_url))

    def test_comment_attachment_is_not_mirrored(self):
        comment = self.ticket.add_comment("Comment", "internal note")
        self.addCleanup(frappe.delete_doc, "Comment", comment.name, force=True)
        file = self.attach("Comment", comment.name)
        self.assertEqual(self.ticket_rows(file.file_url), 0)
        self.assertFalse(self.readable_by(CUSTOMER, file.file_url))

    def test_mirror_is_not_duplicated(self):
        file = self.attach("Communication", self.email().name)
        frappe.get_doc("File", file.name).run_method("after_insert")
        self.assertEqual(self.ticket_rows(file.file_url), 1)

    def test_strip_email_file_ids_only_for_email_files(self):
        email_file = self.attach("Communication", self.email().name, "inline.png")
        comment = self.ticket.add_comment("Comment", "internal note")
        self.addCleanup(frappe.delete_doc, "Comment", comment.name, force=True)
        comment_file = self.attach("Comment", comment.name, "note.png")
        content = (
            f'<img src="{email_file.file_url}?fid={email_file.name}">'
            f'<img src="{comment_file.file_url}?fid={comment_file.name}">'
        )
        stripped = strip_email_file_ids(content)
        self.assertIn(f'src="{email_file.file_url}"', stripped)
        self.assertIn(f"?fid={comment_file.name}", stripped)

    def test_patch_mirrors_existing_attachments(self):
        file = self.attach("Communication", self.email().name)
        frappe.db.delete(
            "File", {"file_url": file.file_url, "attached_to_doctype": "HD Ticket"}
        )
        self.assertFalse(self.readable_by(CUSTOMER, file.file_url))
        mirror_existing()
        self.assertEqual(self.ticket_rows(file.file_url), 1)
        self.assertTrue(self.readable_by(CUSTOMER, file.file_url))
