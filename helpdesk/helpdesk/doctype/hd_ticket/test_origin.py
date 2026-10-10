import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.api import new
from helpdesk.helpdesk.doctype.hd_ticket.origin import ORIGIN_FIELDS, SEARCH_LENGTH
from helpdesk.test_utils import make_agent, make_article, make_contact, unique_email


class TestTicketOrigin(IntegrationTestCase):
    """Only the server sets where a portal ticket started, and a bad origin never blocks the ticket."""

    def setUp(self):
        frappe.set_user("Administrator")
        self.customer = make_contact("origin_customer")["user"]
        self.article = make_article()

    def tearDown(self):
        frappe.set_user("Administrator")

    def raise_ticket(self, user: str, origin=None, **doc) -> dict:
        frappe.set_user(user)
        ticket = new({"subject": "Origin", "description": "<p>Origin</p>", **doc}, [], origin)
        frappe.set_user("Administrator")
        self.addCleanup(frappe.delete_doc, "HD Ticket", ticket["name"], force=True)
        return frappe.db.get_value("HD Ticket", ticket["name"], ORIGIN_FIELDS, as_dict=True)

    def test_each_portal_link_is_stored_as_its_entry_point(self):
        cases = {
            "article": "Article",
            "search": "Search",
            "ticket-list": "Ticket List",
            "closed-ticket": "Closed Ticket",
        }
        for sent, stored in cases.items():
            with self.subTest(sent=sent):
                origin = self.raise_ticket(self.customer, {"from": sent})
                self.assertEqual(origin.entry_point, stored)

    def test_a_missing_or_unknown_from_is_a_direct_visit(self):
        # a non-dict origin never gets here: the whitelist's type check refuses it first
        for origin in ({}, {"from": None}, {"from": "banner"}, {"from": ["article"]}):
            with self.subTest(origin=origin):
                self.assertEqual(self.raise_ticket(self.customer, origin).entry_point, "Direct")

    def test_no_origin_leaves_the_fields_empty(self):
        """The agent desk calls the same endpoint without an origin; its tickets are not Direct."""
        agent = make_agent(unique_email("origin_agent"))
        for user in (agent, self.customer):
            with self.subTest(user=user):
                origin = self.raise_ticket(user)
                self.assertFalse(any(origin.values()))

    def test_a_readable_article_is_kept(self):
        origin = self.raise_ticket(self.customer, {"from": "article", "article": self.article})
        self.assertEqual(origin.source_article, self.article)

    def test_an_article_the_customer_cannot_read_is_dropped(self):
        draft = make_article(status="Draft")
        for article in (draft, "no-such-article", ["list"]):
            with self.subTest(article=article):
                origin = self.raise_ticket(self.customer, {"from": "article", "article": article})
                # the entry point still counts, only the unknown detail goes
                self.assertEqual(origin.entry_point, "Article")
                self.assertIsNone(origin.source_article)

    def test_search_text_is_trimmed_and_capped(self):
        origin = self.raise_ticket(self.customer, {"from": "search", "q": "  refund  "})
        self.assertEqual(origin.source_search, "refund")

        origin = self.raise_ticket(self.customer, {"from": "search", "q": "x" * 500})
        self.assertEqual(len(origin.source_search), SEARCH_LENGTH)

        origin = self.raise_ticket(self.customer, {"from": "search", "q": "   "})
        self.assertIsNone(origin.source_search)

    def test_detail_fields_follow_the_entry_point(self):
        """An article sent with a search origin is not stored, and the other way round."""
        origin = self.raise_ticket(
            self.customer, {"from": "search", "q": "refund", "article": self.article}
        )
        self.assertIsNone(origin.source_article)

        origin = self.raise_ticket(
            self.customer, {"from": "article", "article": self.article, "q": "refund"}
        )
        self.assertIsNone(origin.source_search)

    def test_origin_fields_sent_in_the_doc_are_ignored(self):
        smuggled = {
            "entry_point": "Closed Ticket",
            "source_article": self.article,
            "source_search": "spoofed",
        }
        agent = make_agent(unique_email("origin_agent"))
        # an agent can write the fields directly, so api.new has to drop them itself
        origin = self.raise_ticket(agent, **smuggled)
        self.assertFalse(any(origin.values()))

        origin = self.raise_ticket(self.customer, {"from": "ticket-list"}, **smuggled)
        self.assertEqual(origin.entry_point, "Ticket List")
        self.assertIsNone(origin.source_article)
        self.assertIsNone(origin.source_search)
