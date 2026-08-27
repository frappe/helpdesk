import frappe
from frappe.desk.doctype.tag.tag import add_tag
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.tags import FIRST_TICKET_TAG, apply_tag, update_tags
from helpdesk.test_utils import create_agent, make_ticket

AGENT_EMAIL = "helpdesk-tag-agent@example.com"


class TestTicketTags(FrappeTestCase):
    """The tag picker sends one batch per edit session to
    `helpdesk.api.tags.update_tags`, which builds on core Tag permissions
    and core add_tag/remove_tag for linking. These tests guard that contract."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_agent(AGENT_EMAIL)
        cls.ticket = make_ticket()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_doc_add_and_remove_tag(self):
        frappe.set_user(AGENT_EMAIL)
        # the ticket overrides core's add_tag, which leaves app/color unset
        self.ticket.add_tag("vip-customer", "Red")

        tag = frappe.get_doc("Tag", "vip-customer")
        self.assertEqual(tag.app, "helpdesk")
        self.assertEqual(tag.color, "Red")
        # the picker lists tags as the agent, not as Administrator
        listed = frappe.get_list("Tag", filters={"app": "helpdesk"}, fields=["name"])
        self.assertIn("vip-customer", [t.name for t in listed])
        self.assertTrue(
            frappe.db.exists(
                "Tag Link",
                {
                    "document_type": "HD Ticket",
                    "document_name": self.ticket.name,
                    "tag": "vip-customer",
                },
            )
        )

        # colour is applied only on creation, and a repeat add is not a dupe
        self.ticket.add_tag("vip-customer", "Blue")
        self.assertEqual(frappe.db.get_value("Tag", "vip-customer", "color"), "Red")
        self.assertEqual(
            frappe.db.get_value("HD Ticket", self.ticket.name, "_user_tags").count(
                "vip-customer"
            ),
            1,
        )

        # core's remove_tag is enough: it unlinks, and ignores a second call
        self.ticket.remove_tag("vip-customer")
        self.ticket.remove_tag("vip-customer")
        self.assertNotIn(
            "vip-customer",
            frappe.db.get_value("HD Ticket", self.ticket.name, "_user_tags") or "",
        )
        self.assertFalse(
            frappe.db.exists(
                "Tag Link",
                {
                    "document_type": "HD Ticket",
                    "document_name": self.ticket.name,
                    "tag": "vip-customer",
                },
            )
        )

        # a comma would corrupt the comma-separated _user_tags column
        self.assertRaises(frappe.ValidationError, self.ticket.add_tag, "a,b")

    def test_claim_desk_tags(self):
        # Desk's tag sidebar mints Tag masters with no app/color; the picker
        # sends them as adds on session close, which claims them for helpdesk
        frappe.set_user(AGENT_EMAIL)
        add_tag("desk-minted", "HD Ticket", self.ticket.name)
        self.assertNotEqual(
            frappe.db.get_value("Tag", "desk-minted", "app"), "helpdesk"
        )

        update_tags(
            "HD Ticket",
            self.ticket.name,
            added=[{"name": "desk-minted", "color": "Gray"}],
        )

        tag = frappe.db.get_value("Tag", "desk-minted", ["app", "color"], as_dict=1)
        self.assertEqual(tag.app, "helpdesk")
        self.assertEqual(tag.color, "Gray")
        self.assertEqual(
            frappe.db.get_value("HD Ticket", self.ticket.name, "_user_tags").count(
                "desk-minted"
            ),
            1,
        )
        # a claim is bookkeeping, not a change: no activity logged
        self.assertFalse(
            frappe.db.exists(
                "HD Ticket Activity",
                {"ticket": self.ticket.name, "action": ["like", "%desk-minted%"]},
            )
        )

    def test_update_tags_applies_batch(self):
        frappe.set_user(AGENT_EMAIL)
        apply_tag("HD Ticket", self.ticket.name, "batch-old")

        # the response carries the new _user_tags, so the picker needs no reload
        user_tags = update_tags(
            "HD Ticket",
            self.ticket.name,
            added=[{"name": "batch-new", "color": "Blue"}, {"name": "batch-plain"}],
            removed=["batch-old"],
        )

        self.assertIn("batch-new", user_tags)
        self.assertIn("batch-plain", user_tags)
        self.assertNotIn("batch-old", user_tags)
        self.assertEqual(frappe.db.get_value("Tag", "batch-new", "color"), "Blue")
        self.assertEqual(frappe.db.get_value("Tag", "batch-plain", "color"), "Gray")

        # one activity for the whole batch
        self.assertTrue(
            frappe.db.exists(
                "HD Ticket Activity",
                {
                    "ticket": self.ticket.name,
                    "action": "added tags batch-new, batch-plain & removed tag batch-old",
                },
            )
        )

        # empty batches are a no-op, not an error
        update_tags("HD Ticket", self.ticket.name)

    def test_first_ticket_is_tagged(self):
        requester = "helpdesk-first-timer@example.com"
        first = make_ticket("First one", raised_by=requester)
        second = make_ticket("Second one", raised_by=requester)

        self.assertIn(
            FIRST_TICKET_TAG,
            frappe.db.get_value("HD Ticket", first.name, "_user_tags"),
        )
        self.assertNotIn(
            FIRST_TICKET_TAG,
            frappe.db.get_value("HD Ticket", second.name, "_user_tags") or "",
        )

    def test_tags_apply_to_any_doctype(self):
        # the endpoint takes doctype/name, so tags are not a ticket feature;
        # only the activity log is, and it stays quiet for other doctypes
        frappe.set_user(AGENT_EMAIL)
        article = frappe.get_doc(
            {"doctype": "HD Article", "title": "Tagging an article"}
        ).insert()

        user_tags = update_tags(
            "HD Article", article.name, added=[{"name": "kb-topic", "color": "Cyan"}]
        )

        self.assertIn("kb-topic", user_tags)
        self.assertEqual(frappe.db.get_value("Tag", "kb-topic", "app"), "helpdesk")
        self.assertTrue(
            frappe.db.exists(
                "Tag Link",
                {
                    "document_type": "HD Article",
                    "document_name": article.name,
                    "tag": "kb-topic",
                },
            )
        )
