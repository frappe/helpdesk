import frappe
from frappe.client import set_value

from helpdesk.api.timeline import get_comment_extras
from helpdesk.extends.comment import MAX_PINNED_COMMENTS
from helpdesk.helpdesk.doctype.hd_ticket.api import merge_ticket
from helpdesk.test_utils import make_ticket
from helpdesk.tests.test_core_comments import AGENT_TWO, CoreCommentsTestCase


class TestPinnedComments(CoreCommentsTestCase):
    def test_pin_limit_per_ticket(self):
        """Any agent pins through the standard API, up to the cap. Editing a
        pinned comment at the cap still saves; unpinning frees a slot."""
        ticket = make_ticket()
        comments = [
            self.make_comment(ticket, f"note {i}")
            for i in range(MAX_PINNED_COMMENTS + 1)
        ]
        frappe.set_user(AGENT_TWO)
        for comment in comments[:MAX_PINNED_COMMENTS]:
            set_value("Comment", comment.name, "is_pinned", 1)

        with self.assertRaises(frappe.ValidationError):
            set_value("Comment", comments[-1].name, "is_pinned", 1)

        set_value("Comment", comments[0].name, "content", "edited while pinned")
        set_value("Comment", comments[0].name, "is_pinned", 0)
        set_value("Comment", comments[-1].name, "is_pinned", 1)
        # the pinned bar numbers pins by this order, oldest first
        pinned = get_comment_extras(ticket.name)["pinned_comments"]
        self.assertEqual(pinned, [comment.name for comment in comments[1:]])

    def test_pins_are_counted_per_ticket(self):
        """A full ticket leaves others free to pin, and still takes a merge
        from a ticket with pins of its own."""
        full, other = make_ticket(), make_ticket()
        for i in range(MAX_PINNED_COMMENTS):
            comment = self.make_comment(full, f"note {i}")
            set_value("Comment", comment.name, "is_pinned", 1)
        comment = self.make_comment(other, "fresh ticket")
        set_value("Comment", comment.name, "is_pinned", 1)
        self.assertTrue(frappe.db.get_value("Comment", comment.name, "is_pinned"))

        merge_ticket(source=other.name, target=full.name)
        pinned = get_comment_extras(full.name)["pinned_comments"]
        self.assertEqual(len(pinned), MAX_PINNED_COMMENTS)
