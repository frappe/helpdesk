from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.article import get_article_stats, search
from helpdesk.search import NUM_RESULTS
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    make_agent_manager,
    make_article,
    make_article_feedback,
    make_search_hit,
    make_search_page,
    unique_email,
)


class TestGetArticleStats(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.published = make_article()
        self.draft = make_article(status="Draft")

    def test_counts_views_likes_and_dislikes_of_one_article(self) -> None:
        frappe.db.set_value("HD Article", self.published, "views", 7)
        for feedback in (1, 1, 2, 0):
            make_article_feedback(self.published, feedback)
        make_article_feedback(self.draft, 1)

        stats = get_article_stats(self.published)

        self.assertEqual(stats, {"views": 7, "likes": 2, "dislikes": 1})

    def test_administrator_reads_stats_of_draft(self) -> None:
        self.assertEqual(get_article_stats(self.draft)["likes"], 0)

    def test_agent_reads_stats_of_draft(self) -> None:
        with self.set_user(create_agent(unique_email("article-agent")).name):
            self.assertEqual(get_article_stats(self.draft)["dislikes"], 0)

    def test_agent_manager_reads_stats_of_draft(self) -> None:
        user = make_agent_manager("article-manager")

        with self.set_user(user):
            self.assertEqual(get_article_stats(self.draft)["likes"], 0)

    def test_customer_reads_stats_of_published_article(self) -> None:
        make_article_feedback(self.published, 1)

        customer = create_contact("Article Customer", unique_email("article-customer"))

        with self.set_user(customer["user"]):
            self.assertEqual(get_article_stats(self.published)["likes"], 1)

    def test_customer_cannot_read_stats_of_unpublished_article(self) -> None:
        archived = make_article(status="Archived")
        customer = create_contact("Article Customer", unique_email("article-customer"))

        for article in (self.draft, archived, "missing-article"):
            with self.subTest(article=article), self.set_user(customer["user"]):
                with self.assertRaises(frappe.PermissionError):
                    get_article_stats(article)

    def test_customer_cannot_read_stats_of_an_agents_only_article(self) -> None:
        internal = make_article(visibility="Agents only")
        customer = create_contact("Article Customer", unique_email("article-customer"))

        with self.set_user(customer["user"]), self.assertRaises(frappe.PermissionError):
            get_article_stats(internal)

    def test_inactive_agent_cannot_read_stats_of_draft(self) -> None:
        agent = create_agent(unique_email("article-agent")).name
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
        hits = [make_search_hit(article) for article in self.articles[:NUM_RESULTS]]
        hd_search.return_value = make_search_page(*hits)

        result = search("  How do I RESET my password?! ")

        self.assertEqual(result, hits)
        hd_search.assert_called_once_with("how do i reset my password", qtype="and")

    def test_fallback_merges_unique_hits_up_to_the_limit(self, hd_search, *_) -> None:
        first, second, *rest = [make_search_hit(article) for article in self.articles]
        hd_search.side_effect = [
            make_search_page(first, second),
            make_search_page(second, *rest),
        ]

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
        published = make_search_hit(self.articles[0])
        stale = [
            make_search_hit(make_article(status="Draft")),
            make_search_hit(make_article(status="Archived")),
            make_search_hit("deleted-article"),
        ]
        hd_search.return_value = make_search_page(published, *stale)
        customer = create_contact("Article Customer", unique_email("article-customer"))

        with self.set_user(customer["user"]):
            result = search("reset password")

        self.assertEqual(result, [published])
