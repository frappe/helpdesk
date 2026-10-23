from itertools import chain
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.search import HelpdeskSearch, search, update_article_index
from helpdesk.test_utils import make_article, make_article_category


class FakeIndex:
    """CI's apt redis has no RediSearch; FT.ADD stores a plain hash."""

    def __init__(self, redis) -> None:
        self.redis = redis

    def info(self) -> dict:
        return {"num_docs": 0}

    def add_document(self, doc_id: str, replace: bool = False, **fields) -> None:
        # raw HSET: doc_id already carries the site prefix
        self.redis.execute_command("HSET", doc_id, *chain(*fields.items()))


class TestArticleIndex(IntegrationTestCase):
    def setUp(self) -> None:
        self.search = HelpdeskSearch()
        redis_class = type(self.search.redis)
        fake_ft = patch.object(redis_class, "ft", lambda redis, _: FakeIndex(redis))
        fake_ft.start()
        # added first, so it stops after unindex has run
        self.addCleanup(fake_ft.stop)

        category = make_article_category("Fixture Index").name
        self.article = make_article(
            category=category, content="<h2>Alpha</h2><p>zebra</p>"
        )
        update_article_index(self.article)
        self.addCleanup(self.unindex)

    def unindex(self) -> None:
        frappe.db.set_value("HD Article", self.article, "status", "Draft")
        update_article_index(self.article)

    def headings(self) -> set[str]:
        pattern = self.search.redis.make_key(
            f"{self.search.prefix}:HD Article:{self.article}#*"
        )
        return {
            key.decode().rsplit("#", 1)[1]
            for key in self.search.redis.scan_iter(match=pattern)
        }

    def test_an_edit_replaces_the_old_sections(self) -> None:
        self.assertIn("alpha", self.headings())

        frappe.db.set_value(
            "HD Article", self.article, "content", "<h2>Beta</h2><p>zebra</p>"
        )
        update_article_index(self.article)

        self.assertIn("beta", self.headings())
        self.assertNotIn("alpha", self.headings())

    def test_unpublishing_drops_the_article(self) -> None:
        frappe.db.set_value("HD Article", self.article, "status", "Draft")
        update_article_index(self.article)

        self.assertEqual(self.headings(), set())

    def test_saving_queues_the_update(self) -> None:
        with patch("frappe.enqueue") as enqueue:
            frappe.get_doc("HD Article", self.article).save()

        enqueue.assert_called_once()
        self.assertEqual(
            enqueue.call_args.args[0], "helpdesk.search.update_article_index"
        )
        self.assertEqual(enqueue.call_args.kwargs["article"], self.article)


class TestSearchQuery(IntegrationTestCase):
    def test_the_last_word_is_a_prefix_only(self) -> None:
        with patch.object(HelpdeskSearch, "search") as search_index:
            search_index.return_value.docs = []
            search("restore backup autho")
        # "autho" may be half typed: no fuzzy, or it matches "auto"
        self.assertEqual(
            search_index.call_args.args[0],
            "(%restore%|restore*) (%backup%|backup*) autho*",
        )
