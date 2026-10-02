import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_datetime

from helpdesk.extends.file import strip_email_file_ids
from helpdesk.helpdesk.doctype.hd_ticket.api import split_ticket
from helpdesk.patches.mirror_email_attachments_to_tickets import (
    execute as mirror_existing,
)
from helpdesk.test_utils import (
    attach_private_file,
    can_download,
    count_ticket_files,
    create_contact,
    make_agent,
    make_customer_ticket,
    make_ticket_email,
)

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

    def email_file(self, sent_or_received="Received", file_name="invoice.txt"):
        email = make_ticket_email(self, self.ticket.name, CUSTOMER, sent_or_received)
        return attach_private_file(self, "Communication", email.name, file_name)

    def test_customer_reads_attachment_of_received_email(self):
        file = self.email_file()
        self.assertEqual(count_ticket_files(self.ticket.name, file.file_url), 1)
        self.assertTrue(can_download(CUSTOMER, file.file_url))
        self.assertTrue(can_download(AGENT, file.file_url))

    def test_customer_reads_attachment_of_sent_email(self):
        file = self.email_file("Sent")
        self.assertTrue(can_download(CUSTOMER, file.file_url))

    def test_other_customer_cannot_read_attachment(self):
        file = self.email_file()
        self.assertFalse(can_download(OTHER_CUSTOMER, file.file_url))

    def test_comment_attachment_is_not_mirrored(self):
        comment = self.ticket.add_comment("Comment", "internal note")
        self.addCleanup(frappe.delete_doc, "Comment", comment.name, force=True)
        file = attach_private_file(self, "Comment", comment.name)
        self.assertEqual(count_ticket_files(self.ticket.name, file.file_url), 0)
        self.assertFalse(can_download(CUSTOMER, file.file_url))

    def test_mirror_is_not_duplicated(self):
        file = self.email_file()
        frappe.get_doc("File", file.name).run_method("after_insert")
        self.assertEqual(count_ticket_files(self.ticket.name, file.file_url), 1)

    def test_mirror_keeps_file_timestamps(self):
        file = self.email_file()
        mirror = frappe.db.get_value(
            "File",
            {"file_url": file.file_url, "attached_to_doctype": "HD Ticket"},
            ["creation", "owner"],
            as_dict=True,
        )
        self.assertEqual(mirror.creation, get_datetime(file.creation))
        self.assertEqual(mirror.owner, file.owner)

    def test_strip_email_file_ids_only_for_email_files(self):
        email = make_ticket_email(self, self.ticket.name, CUSTOMER)
        email_file = attach_private_file(
            self, "Communication", email.name, "inline.png"
        )
        comment = self.ticket.add_comment("Comment", "internal note")
        self.addCleanup(frappe.delete_doc, "Comment", comment.name, force=True)
        comment_file = attach_private_file(self, "Comment", comment.name, "note.png")
        content = (
            f'<img src="{email_file.file_url}?fid={email_file.name}">'
            f'<img src="{comment_file.file_url}?fid={comment_file.name}">'
        )
        emails = [frappe._dict(name=email.name, content=content)]
        strip_email_file_ids(emails)
        self.assertIn(f'src="{email_file.file_url}"', emails[0].content)
        self.assertIn(f"?fid={comment_file.name}", emails[0].content)

    def test_patch_mirrors_existing_attachments(self):
        file = self.email_file()
        frappe.db.delete(
            "File", {"file_url": file.file_url, "attached_to_doctype": "HD Ticket"}
        )
        self.assertFalse(can_download(CUSTOMER, file.file_url))
        mirror_existing()
        self.assertEqual(count_ticket_files(self.ticket.name, file.file_url), 1)
        self.assertTrue(can_download(CUSTOMER, file.file_url))

    def test_split_keeps_backfilled_mirror_with_its_email(self):
        file = self.email_file()
        frappe.db.delete(
            "File", {"file_url": file.file_url, "attached_to_doctype": "HD Ticket"}
        )
        later = make_ticket_email(self, self.ticket.name, CUSTOMER)
        mirror_existing()
        new_ticket = split_ticket("Split", later.name)
        self.addCleanup(frappe.delete_doc, "HD Ticket", new_ticket, force=True)
        self.assertEqual(count_ticket_files(self.ticket.name, file.file_url), 1)
        self.assertEqual(count_ticket_files(new_ticket, file.file_url), 0)

    def test_strip_email_file_ids_only_for_given_emails(self):
        other = make_customer_ticket(self, raised_by=OTHER_CUSTOMER)
        other_email = make_ticket_email(self, other.name, OTHER_CUSTOMER)
        other_file = attach_private_file(self, "Communication", other_email.name)
        email = make_ticket_email(self, self.ticket.name, CUSTOMER)
        content = f'<img src="{other_file.file_url}?fid={other_file.name}">'
        emails = [frappe._dict(name=email.name, content=content)]
        strip_email_file_ids(emails)
        self.assertEqual(emails[0].content, content)

    def test_strip_email_file_ids_across_emails(self):
        emails = []
        for _ in range(2):
            email = make_ticket_email(self, self.ticket.name, CUSTOMER)
            file = attach_private_file(self, "Communication", email.name, "inline.png")
            emails.append(
                frappe._dict(
                    name=email.name,
                    content=f'<img src="{file.file_url}?fid={file.name}">',
                )
            )
        strip_email_file_ids(emails)
        self.assertTrue(all("?fid=" not in email.content for email in emails))
