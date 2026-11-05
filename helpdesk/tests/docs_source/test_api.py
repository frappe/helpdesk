from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.docs_source import (
    connect_docs_source,
    disconnect_docs_source,
    get_doc_page,
    get_docs_source,
    resync_docs_source,
    search_docs,
    set_hidden_sections,
)
from helpdesk.docs_source import DocsSource, get_source
from helpdesk.docs_source.fetch import DocsFetchError
from helpdesk.docs_source.index import DocsIndex
from helpdesk.docs_source.llms import LlmsSource
from helpdesk.docs_source.sitemap import SitemapSource
from helpdesk.docs_source.wiki import WikiSource
from helpdesk.test_utils import create_agent, make_agent_manager, make_article, unique_email

URL = "https://docs.example.com"
API = "helpdesk.api.docs_source"
EMPTY = {
    "docs_source_url": "",
    "docs_source_type": "",
    "docs_source_label": "",
    "docs_source_hidden_sections": "",
}


class FakeSource(DocsSource):
    def __init__(self, hits=(), pages=None, sections=()):
        self.hits, self.pages, self._sections = list(hits), pages or {}, list(sections)

    def search(self, query):
        return self.hits

    def get_page(self, route):
        if route not in self.pages:
            raise frappe.DoesNotExistError
        return dict(self.pages[route])

    def sections(self):
        return self._sections


def hit(route, title):
    return {"route": route, "title": title, "excerpt": "x", "category_label": "L"}


class DocsCase(IntegrationTestCase):
    def setUp(self):
        self.enterContext(change_settings("HD Settings", EMPTY))
        self.sync = self.enterContext(patch(f"{API}.enqueue_sync"))
        self.addCleanup(DocsIndex().clear)

    def connect_as_llms(self, url=URL):
        with (
            patch.object(WikiSource, "is_available", return_value=False),
            patch.object(LlmsSource, "is_available", return_value=True),
        ):
            return connect_docs_source(url)

    def connect_as_wiki(self, url=URL):
        with patch.object(WikiSource, "is_available", return_value=True):
            return connect_docs_source(url)


class TestConnect(DocsCase):
    def test_connect_order_is_wiki_llms_sitemap(self):
        calls = []

        def probe(name, result):
            def available(self):
                calls.append(name)
                return result

            return available

        for wiki, llms, sitemap, expected_type, expected_calls in [
            (True, True, True, "Frappe Wiki", ["wiki"]),
            (False, True, True, "llms.txt", ["wiki", "llms"]),
            (False, False, True, "Sitemap", ["wiki", "llms", "sitemap"]),
        ]:
            calls.clear()
            with (
                patch.object(WikiSource, "is_available", probe("wiki", wiki)),
                patch.object(LlmsSource, "is_available", probe("llms", llms)),
                patch.object(SitemapSource, "is_available", probe("sitemap", sitemap)),
            ):
                connect_docs_source(URL)
            self.assertEqual(calls, expected_calls)
            self.assertEqual(frappe.db.get_single_value("HD Settings", "docs_source_type"), expected_type)
            disconnect_docs_source()

    def test_connect_refuses_http_and_unknown_sites(self):
        for bad in (
            "http://docs.example.com",
            "https://",
            "docs.example.com",
            "https://user:pw@docs.example.com",
            "https://docs.example.com?a=1",
            "https://docs.example.com/#top",
            "https://docs.example.com/x?",
        ):
            with self.assertRaises(frappe.ValidationError, msg=bad):
                connect_docs_source(bad)
        with (
            patch.object(WikiSource, "is_available", return_value=False),
            patch.object(LlmsSource, "is_available", return_value=False),
            patch.object(SitemapSource, "is_available", return_value=False),
        ):
            with self.assertRaisesRegex(frappe.ValidationError, "no Frappe Wiki, llms.txt or sitemap"):
                connect_docs_source(URL)
        self.assertFalse(frappe.db.get_single_value("HD Settings", "docs_source_url"))

    def test_connect_strips_trailing_slashes_and_stores_fields(self):
        self.connect_as_wiki(f"{URL}/docs//")
        get = lambda f: frappe.db.get_single_value("HD Settings", f)
        self.assertEqual(get("docs_source_url"), f"{URL}/docs")
        self.assertEqual(get("docs_source_type"), "Frappe Wiki")
        self.assertEqual(get("docs_source_label"), "Frappe Wiki")

    def test_connect_refuses_when_already_connected(self):
        self.connect_as_wiki()
        with self.assertRaisesRegex(frappe.ValidationError, "Disconnect the current docs source first."):
            self.connect_as_wiki("https://other.example.com")
        self.assertEqual(frappe.db.get_single_value("HD Settings", "docs_source_url"), URL)

    def test_connect_wiki_runs_no_sync(self):
        self.connect_as_wiki()
        self.sync.assert_not_called()

    def test_connect_indexed_site_enqueues_sync(self):
        self.connect_as_llms()
        self.sync.assert_called_once()

    def test_connect_resets_other_docs_fields(self):
        frappe.db.set_single_value(
            "HD Settings",
            {"docs_source_page_count": 9, "docs_source_sync_error": "old", "docs_source_hidden_sections": '["a"]'},
        )
        self.connect_as_llms()
        get = lambda f: frappe.db.get_single_value("HD Settings", f)
        self.assertEqual(get("docs_source_page_count"), 0)
        self.assertFalse(get("docs_source_sync_error"))
        self.assertFalse(get("docs_source_hidden_sections"))

    def test_settings_cache_is_fresh_after_writes(self):
        frappe.get_cached_doc("HD Settings")  # warm the cache
        self.assertIsNone(get_source())
        self.connect_as_llms()
        self.assertIsInstance(get_source(), LlmsSource)
        self.assertEqual(frappe.get_cached_doc("HD Settings").docs_source_url, URL)
        disconnect_docs_source()
        self.assertIsNone(get_source())
        self.assertFalse(frappe.get_cached_doc("HD Settings").docs_source_url)


class TestManage(DocsCase):
    def test_writes_need_settings_write(self):
        self.connect_as_wiki()
        agent = create_agent(unique_email("plain-agent")).name
        with self.set_user(agent):
            for call in (
                lambda: connect_docs_source("https://other.example.com"),
                disconnect_docs_source,
                resync_docs_source,
                lambda: set_hidden_sections([]),
            ):
                with self.assertRaises(frappe.PermissionError):
                    call()
            self.assertEqual(get_docs_source()["url"], URL)
        self.assertEqual(frappe.db.get_single_value("HD Settings", "docs_source_url"), URL)

    def test_agent_manager_can_write(self):
        with self.set_user(make_agent_manager()):
            self.connect_as_wiki()
            disconnect_docs_source()
        self.assertFalse(frappe.db.get_single_value("HD Settings", "docs_source_url"))

    def test_disconnect_clears_fields_and_index(self):
        self.connect_as_llms()
        frappe.db.set_single_value(
            "HD Settings", {"docs_source_page_count": 4, "docs_source_synced_on": "2026-01-01 10:00:00"}
        )
        with patch.object(DocsIndex, "clear") as clear:
            disconnect_docs_source()
        clear.assert_called_once()
        for field in (
            "docs_source_url",
            "docs_source_type",
            "docs_source_label",
            "docs_source_page_count",
        ):
            self.assertFalse(frappe.db.get_single_value("HD Settings", field), field)
        self.assertFalse(frappe.get_cached_doc("HD Settings").docs_source_synced_on)

    def test_resync(self):
        with self.assertRaises(frappe.ValidationError):
            resync_docs_source()
        self.connect_as_wiki()
        with self.assertRaises(frappe.ValidationError):
            resync_docs_source()
        self.sync.assert_not_called()
        disconnect_docs_source()
        self.connect_as_llms()
        self.sync.reset_mock()
        resync_docs_source()
        self.sync.assert_called_once()

    def test_set_hidden_sections(self):
        sections = [{"key": "a", "title": "A"}, {"key": "b", "title": "B"}]
        with self.assertRaises(frappe.ValidationError):
            set_hidden_sections(["a"])
        self.connect_as_wiki()
        with patch.object(WikiSource, "sections", return_value=sections):
            with self.assertRaises(frappe.ValidationError):
                set_hidden_sections(["zzz"])
            set_hidden_sections(["b", "b"])
        self.assertEqual(frappe.db.get_single_value("HD Settings", "docs_source_hidden_sections"), '["b"]')
        self.assertEqual(get_source().hidden, ["b"])

    def test_set_hidden_sections_refused_for_indexed_sites(self):
        self.connect_as_llms()
        with self.assertRaises(frappe.ValidationError):
            set_hidden_sections([])

    def test_get_docs_source(self):
        self.assertIsNone(get_docs_source())
        self.connect_as_wiki()
        with patch.object(WikiSource, "sections", return_value=[{"key": "a", "title": "A"}]):
            info = get_docs_source()
        self.assertEqual(info["url"], URL)
        self.assertEqual(info["type"], "Frappe Wiki")
        self.assertEqual(info["sections"], [{"key": "a", "title": "A", "hidden": False}])
        self.assertFalse(info["sections_error"])
        with patch.object(WikiSource, "sections", side_effect=DocsFetchError("down")):
            info = get_docs_source()
        self.assertEqual((info["sections"], info["sections_error"]), ([], True))


class TestReaders(DocsCase):
    def test_no_source_returns_nothing(self):
        self.assertEqual(search_docs("anything"), [])
        with self.assertRaises(frappe.DoesNotExistError):
            get_doc_page("a/b")

    def test_guest_blocked_when_kb_private(self):
        self.connect_as_wiki()
        with change_settings("HD Settings", {"public_knowledge_base": 0}):
            with self.set_user("Guest"):
                with self.assertRaises(frappe.PermissionError):
                    search_docs("x")
                with self.assertRaises(frappe.PermissionError):
                    get_doc_page("a/b")

    def test_source_down_returns_nothing(self):
        self.connect_as_wiki()
        with (
            patch.object(WikiSource, "search", side_effect=DocsFetchError("down")),
            patch.object(WikiSource, "get_page", side_effect=DocsFetchError("down")),
        ):
            self.assertEqual(search_docs("x"), [])
            with self.assertRaises(frappe.DoesNotExistError):
                get_doc_page("a/b")

    def test_search_trims_and_caps_limit(self):
        hits = [hit(f"a/{i}", f"T{i}") for i in range(9)]
        self.connect_as_wiki()
        with patch(f"{API}.get_source", return_value=FakeSource(hits)):
            self.assertEqual(len(search_docs("x", limit=50)), 4)
            self.assertEqual(len(search_docs("x", limit="2")), 2)
            self.assertEqual(len(search_docs("x", limit=-3)), 4)
            self.assertEqual(search_docs("   "), [])


class TestRelated(DocsCase):
    def related(self, hits, articles=(), route="a/page", title="Page"):
        source = FakeSource(hits, {route: {"title": title}})
        rows = [{"name": n, "title": t, "title_slug": t.lower()} for n, t in articles]
        with (
            patch(f"{API}.get_source", return_value=source),
            patch(f"{API}.get_related", return_value=rows),
        ):
            return get_doc_page(route)["related"]

    def test_related_docs_stay_in_section(self):
        found = self.related(
            [hit("a/page", "Page"), hit("a/one", "One"), hit("b/two", "Two")]
        )
        self.assertEqual(found["docs"], [{"route": "a/one", "title": "One"}])

    def test_related_docs_are_plain_deduped_and_capped(self):
        hits = [hit("a/x", "<mark>Same</mark> &amp; <b>co</b>"), hit("a/y", "Same & co")]
        hits += [hit(f"a/{i}", f"T{i}") for i in range(9)]
        docs = self.related(hits)["docs"]
        self.assertEqual(docs[0], {"route": "a/x", "title": "Same & co"})
        self.assertEqual(len(docs), 6)
        self.assertNotIn("a/y", [d["route"] for d in docs])

    def test_related_drops_docs_with_matching_article_title(self):
        article = make_article()
        title = frappe.db.get_value("HD Article", article, "title")
        found = self.related([hit("a/one", title), hit("a/two", "Other")], [(article, title)])
        self.assertEqual([d["route"] for d in found["docs"]], ["a/two"])
        self.assertEqual([a["name"] for a in found["articles"]], [article])

    def test_related_ignores_converted_article_titles(self):
        article = make_article(docs_page_route="a/one")
        title = frappe.db.get_value("HD Article", article, "title")
        found = self.related([hit("a/one", title)], [(article, title)])
        self.assertEqual([d["route"] for d in found["docs"]], ["a/one"])

    def test_failed_related_reads_do_not_fail_the_page(self):
        source = FakeSource([], {"a/page": {"title": "Page"}})
        source.search = lambda q: (_ for _ in ()).throw(DocsFetchError("down"))
        with (
            patch(f"{API}.get_source", return_value=source),
            patch(f"{API}.get_related", side_effect=RuntimeError("boom")),
            patch(f"{API}.frappe.log_error"),
        ):
            page = get_doc_page("a/page")
        self.assertEqual(page["related"], {"docs": [], "articles": []})
        self.assertEqual(page["title"], "Page")
