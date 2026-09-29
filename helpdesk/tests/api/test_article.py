from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.article import get_article_stats, search
from helpdesk.search import NUM_RESULTS
from helpdesk.test_utils import create_agent, create_contact


def make_article(status: str = "Published") -> str:
    """Insert an HD Article with a unique title and return its name."""
    return (
        frappe.get_doc(
            {
                "doctype": "HD Article",
                "title": f"Reset password {frappe.generate_hash(length=6)}",
                "content": "<p>Open settings and click reset.</p>",
                "status": status,
            }
        )
        .insert(ignore_permissions=True)
        .name
    )


def add_feedback(article: str, feedback: int) -> None:
    frappe.get_doc(
        {
            "doctype": "HD Article Feedback",
            "user": "Administrator",
            "article": article,
            "feedback": feedback,
        }
    ).insert(ignore_permissions=True)


def make_customer_user() -> str:
    email = f"article-customer-{frappe.generate_hash(length=6)}@example.com"
    return create_contact("Article Customer", email)["user"]


def make_agent_user() -> str:
    email = f"article-agent-{frappe.generate_hash(length=6)}@example.com"
    return create_agent(email).name


def search_hit(article: str, section: str = "intro") -> frappe._dict:
    """A search index hit shaped like helpdesk.search.search items."""
    name = f"{article}#{section}"
    return frappe._dict(id=f"HD Article:{name}", name=name, subject=article)


def search_page(*hits: frappe._dict) -> list[dict]:
    return [{"title": "Articles", "items": list(hits)}]


class TestGetArticleStats(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.published = make_article()
        self.draft = make_article("Draft")

    def test_counts_views_likes_and_dislikes_of_one_article(self) -> None:
        frappe.db.set_value("HD Article", self.published, "views", 7)
        for feedback in (1, 1, 2, 0):
            add_feedback(self.published, feedback)
        add_feedback(self.draft, 1)

        stats = get_article_stats(self.published)

        self.assertEqual(stats, {"views": 7, "likes": 2, "dislikes": 1})

    def test_administrator_reads_stats_of_draft(self) -> None:
        self.assertEqual(get_article_stats(self.draft)["likes"], 0)

    def test_agent_reads_stats_of_draft(self) -> None:
        with self.set_user(make_agent_user()):
            self.assertEqual(get_article_stats(self.draft)["dislikes"], 0)

    def test_agent_manager_reads_stats_of_draft(self) -> None:
        user = make_agent_user()
        frappe.get_doc("User", user).add_roles("Agent Manager")

        with self.set_user(user):
            self.assertEqual(get_article_stats(self.draft)["likes"], 0)

    def test_customer_reads_stats_of_published_article(self) -> None:
        add_feedback(self.published, 1)

        with self.set_user(make_customer_user()):
            self.assertEqual(get_article_stats(self.published)["likes"], 1)

    def test_customer_cannot_read_stats_of_unpublished_article(self) -> None:
        archived = make_article("Archived")
        customer = make_customer_user()

        for article in (self.draft, archived, "missing-article"):
            with self.subTest(article=article), self.set_user(customer):
                with self.assertRaises(frappe.PermissionError):
                    get_article_stats(article)

    def test_inactive_agent_cannot_read_stats_of_draft(self) -> None:
        agent = make_agent_user()
        frappe.db.set_value("HD Agent", agent, "is_active", 0)

        with self.set_user(agent), self.assertRaises(frappe.PermissionError):
            get_article_stats(self.draft)


@patch("helpdesk.api.article.get_nouns", return_value=[])
@patch("helpdesk.api.article.get_noun_phrases", return_value=["password reset"])
@patch("helpdesk.api.article.hd_search")
class TestSearchArticles(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.articles = [make_article() for _ in range(NUM_RESULTS + 1)]

    def test_full_first_page_is_returned_without_fallback(self, hd_search, *_) -> None:
        hits = [search_hit(article) for article in self.articles[:NUM_RESULTS]]
        hd_search.return_value = search_page(*hits)

        result = search("  How do I RESET my password?! ")

        self.assertEqual(result, hits)
        hd_search.assert_called_once_with("how do i reset my password", qtype="and")

    def test_fallback_merges_unique_hits_up_to_the_limit(self, hd_search, *_) -> None:
        first, second, *rest = [search_hit(article) for article in self.articles]
        hd_search.side_effect = [search_page(first, second), search_page(second, *rest)]

        result = search("reset my password")

        self.assertEqual(result, [first, second, *rest][:NUM_RESULTS])
        hd_search.assert_called_with("password reset", qtype="and")

    def test_no_match_returns_empty_list(self, hd_search, *_) -> None:
        hd_search.return_value = []

        self.assertEqual(search("nothing matches this"), [])
        self.assertEqual(hd_search.call_count, 3)

    def test_customer_never_sees_unpublished_article_from_stale_index(
        self, hd_search, *_
    ) -> None:
        published = search_hit(self.articles[0])
        stale = [
            search_hit(make_article("Draft")),
            search_hit(make_article("Archived")),
            search_hit("deleted-article"),
        ]
        hd_search.return_value = search_page(published, *stale)

        with self.set_user(make_customer_user()):
            result = search("reset password")

        self.assertEqual(result, [published])
