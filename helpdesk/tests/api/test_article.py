import inspect
from unittest.mock import PropertyMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from textblob import TextBlob
from textblob.exceptions import MissingCorpusError

from helpdesk.api.article import (
    _search,
    get_article_stats,
    get_noun_phrases,
    get_nouns,
    search,
)
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

    def test_customer_cannot_read_stats_of_an_private_article(self) -> None:
        internal = make_article(visibility="Private")
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
        hd_search.assert_called_once_with(
            "how do i reset my password", qtype="and", limit=NUM_RESULTS
        )

    def test_fallback_merges_unique_hits_up_to_the_limit(self, hd_search, *_) -> None:
        first, second, *rest = [make_search_hit(article) for article in self.articles]
        hd_search.side_effect = [
            make_search_page(first, second),
            make_search_page(second, *rest),
        ]

        result = search("reset my password")

        self.assertEqual(result, [first, second, *rest][:NUM_RESULTS])
        hd_search.assert_called_with("password reset", qtype="and", limit=NUM_RESULTS)

    def test_sections_of_one_article_count_once(self, hd_search, *_) -> None:
        long_article, *others = self.articles
        sections = [
            make_search_hit(long_article, f"section-{i}") for i in range(NUM_RESULTS)
        ]
        other_hits = [make_search_hit(article) for article in others]
        hd_search.side_effect = [
            make_search_page(*sections),
            make_search_page(*other_hits),
        ]

        result = search("reset my password")

        self.assertEqual(result, [sections[0], *other_hits][:NUM_RESULTS])

    def test_search_passes_the_hit_limit(self, hd_search, *_) -> None:
        hd_search.return_value = make_search_page(make_search_hit(self.articles[0]))

        _search("reset my password", limit=200)

        self.assertEqual(hd_search.call_args.kwargs["limit"], 200)

    def test_whitelisted_search_cannot_request_more_than_the_default(
        self, hd_search, *_
    ) -> None:
        hd_search.return_value = make_search_page(make_search_hit(self.articles[0]))

        self.assertEqual(list(inspect.signature(search).parameters), ["query"])
        self.assertRaises(TypeError, search, "reset my password", limit=100000)
        search("reset my password")
        self.assertEqual(hd_search.call_args.kwargs["limit"], NUM_RESULTS)

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


class TestMissingCorpus(IntegrationTestCase):
    def test_search_without_nltk_data_finds_no_nouns(self):
        # a site without the NLTK corpora must not fail the search
        blob = TextBlob("reset my password")
        with (
            patch.object(TextBlob, "pos_tags", new_callable=PropertyMock) as pos_tags,
            patch.object(
                TextBlob, "noun_phrases", new_callable=PropertyMock
            ) as noun_phrases,
        ):
            pos_tags.side_effect = noun_phrases.side_effect = MissingCorpusError()
            self.assertEqual(get_nouns(blob), [])
            self.assertEqual(get_noun_phrases(blob), [])
