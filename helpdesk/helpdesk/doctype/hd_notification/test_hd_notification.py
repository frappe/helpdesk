# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDNotification(FrappeTestCase):
    def test_should_push(self):
        # Push assignment, mention and ticket reopen; skip comment emoji-reactions.
        cases = [
            ("Assignment", None, True),
            ("Mention", "comment-1", True),
            ("Reaction", None, True),  # ticket reopen
            ("Reaction", "comment-1", False),  # emoji reaction on a comment
        ]
        for notification_type, reference_comment, expected in cases:
            doc = frappe.new_doc("HD Notification")
            doc.notification_type = notification_type
            doc.reference_comment = reference_comment
            self.assertEqual(doc.should_push(), expected, msg=notification_type)
