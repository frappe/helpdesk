from contextlib import contextmanager
from unittest.mock import patch

import frappe
import frappe.website.utils
from frappe.tests.utils import change_settings

from helpdesk.api.docs_source import (
    bulk_convert_docs_pages,
    convert_docs_page,
    get_bulk_convert_result,
    get_doc_page,
    list_docs_pages,
    search_docs,
)
from helpdesk.api.knowledge_base import get_article
from helpdesk.docs_source.convert import (
    MAX_BULK,
    convert_page,
    converted_article,
    mark_pages,
    readable_converted_routes,
    result_key,
    run_bulk,
)
from helpdesk.docs_source.fetch import DOWN_KEY, DocsFetchError
from helpdesk.docs_source.wiki import WikiSource
from helpdesk.test_utils import (
    article_index_jobs,
    DocsCase,
    FakeSource,
    create_agent,
    docs_hit as hit,
    make_agent_manager,
    make_article,
    make_article_category,
    make_contact,
    unique_email,
    unique_name,
)

API = "helpdesk.api.docs_source"
HOOK = "helpdesk.helpdesk.doctype.hd_article.hd_article.capture_event"
CONVERT = "helpdesk.docs_source.convert"


class ConvertCase(DocsCase):
    def setUp(self):
        super().setUp()
        self.title = unique_name("Setup")
        self.route = unique_name("helpdesk/setup")
        self.other = unique_name("helpdesk/other")
        self.source_url = f"https://docs.example.com/{self.route}"
        self.category = make_article_category(unique_name("Convert")).name
        self.pages = {
            self.route: {"title": self.title, "content": "<p>Body</p>", "source_url": self.source_url},
            self.other: {"title": unique_name("Other"), "content": "<p>x</p>", "source_url": "u"},
        }
        self.source = FakeSource([hit(self.route, self.title)], self.pages)
        for target in (f"{API}.get_source", f"{CONVERT}.get_source"):
            self.enterContext(patch(target, return_value=self.source))
        self.enterContext(patch(f"{API}.get_related", return_value=[]))
        self.enterContext(patch(f"{CONVERT}.time.sleep"))
        self.agent = create_agent(unique_email("convert-agent")).name
        self.manager = make_agent_manager("convert-manager")
        self.customer = make_contact("convert-customer")["user"]

    def convert(self, route=None):
        with self.set_user(self.agent):
            return convert_docs_page(route or self.route, self.category)

    @contextmanager
    def job_db(self):
        """Commit and rollback act on a savepoint, so the test's own data survives."""
        rollback = frappe.db.rollback
        frappe.db.savepoint("job")
        with (
            patch("frappe.db.commit", side_effect=lambda: frappe.db.savepoint("job")) as commit,
            patch("frappe.db.rollback", side_effect=lambda: rollback(save_point="job")),
        ):
            yield commit

    def field(self, article, name):
        return frappe.db.get_value("HD Article", article, name)


class TestConvert(ConvertCase):
    def test_convert_makes_a_draft_in_the_category(self):
        with self.set_user(self.agent):
            name = convert_page(self.route, self.category)
        article = frappe.get_doc("HD Article", name)
        self.assertEqual((article.status, article.category), ("Draft", self.category))
        self.assertEqual((article.title, article.content), (self.title, "<p>Body</p>"))
        self.assertEqual((article.docs_page_route, article.docs_page_url), (self.route, self.source_url))
        self.assertEqual(article.author, self.agent)

    def test_views_start_at_zero_and_stamp_is_set(self):
        article = frappe.get_doc("HD Article", self.convert())
        self.assertEqual(article.views, 0)
        self.assertTrue(article.docs_copied_on)

    def test_final_route_after_a_redirect_is_stored(self):
        self.pages["old/path"] = {**self.pages[self.route], "route": self.route}
        article = self.convert("old/path")
        self.assertEqual(self.field(article, "docs_page_route"), self.route)

    def test_a_long_route_and_url_are_stored(self):
        route = "helpdesk/" + "x" * 400
        self.pages[route] = {**self.pages[self.route], "source_url": "https://docs.example.com/" + "y" * 900}
        article = self.convert(route)
        self.assertEqual(self.field(article, "docs_page_route"), route)
        self.assertEqual(len(self.field(article, "docs_page_url")), 925)

    def test_long_title_is_cut_to_140(self):
        self.pages[self.route]["title"] = "<b>Long</b> " + "x" * 300
        article = self.convert()
        self.assertEqual(len(self.field(article, "title")), 140)

    def test_second_convert_is_refused_in_any_status(self):
        article = self.convert()
        for status in ("Draft", "Published", "Archived"):
            frappe.db.set_value("HD Article", article, "status", status)
            with self.assertRaises(frappe.ValidationError):
                self.convert()
        self.assertEqual(frappe.db.count("HD Article", {"docs_page_route": self.route}), 1)

    def test_deleted_article_allows_convert_again(self):
        make_article(category=self.category)  # a category keeps one article
        frappe.delete_doc("HD Article", self.convert(), force=True)
        self.assertTrue(self.convert())

    def test_matching_article_does_not_block_convert(self):
        make_article(self.title)
        self.assertTrue(self.convert())

    def test_same_title_pages_in_one_run_all_convert(self):
        for i in range(3):
            self.pages[f"{self.route}-d{i}"] = {**self.pages[self.route], "source_url": f"u{i}"}
        routes = [f"{self.route}-d{i}" for i in range(3)]
        with self.job_db():
            run_bulk(routes, self.category, self.manager)
        self.assertEqual(frappe.db.count("HD Article", {"docs_page_route": ["in", routes]}), 3)

    def test_customer_cannot_convert(self):
        with self.set_user(self.customer), self.assertRaises(frappe.PermissionError):
            convert_docs_page(self.route, self.category)
        self.assertFalse(frappe.db.exists("HD Article", {"docs_page_route": self.route}))

    def test_convert_refuses_bad_category_hidden_page_and_no_source(self):
        with self.set_user(self.agent):
            with self.assertRaises(frappe.DoesNotExistError):
                convert_docs_page(self.route, "nope")
            with self.assertRaises(frappe.DoesNotExistError):
                convert_docs_page("hidden/page", self.category)
        with patch(f"{CONVERT}.get_source", return_value=None):
            with self.assertRaisesRegex(frappe.ValidationError, "No docs source"):
                self.convert()

    def test_fetch_error_becomes_a_clear_message(self):
        self.source.get_page = lambda route, live=True: (_ for _ in ()).throw(DocsFetchError("HTTP 500"))
        with self.assertRaisesRegex(frappe.ValidationError, "could not be read"):
            self.convert()

    def test_source_change_leaves_article_untouched(self):
        article = self.convert()
        self.pages[self.route]["content"] = "<p>Changed</p>"
        self.assertEqual(self.field(article, "content"), "<p>Body</p>")


class TestBulk(ConvertCase):
    def test_agent_cannot_bulk_convert(self):
        with self.set_user(self.agent), self.assertRaises(frappe.PermissionError):
            bulk_convert_docs_pages([self.route], self.category)

    def test_manager_enqueues_on_long_after_commit(self):
        with self.set_user(self.manager), patch(f"{API}.frappe.enqueue") as enqueue:
            bulk_convert_docs_pages([self.route, self.route], self.category)
        kwargs = enqueue.call_args.kwargs
        self.assertEqual((kwargs["queue"], kwargs["enqueue_after_commit"]), ("long", True))
        self.assertEqual(kwargs["routes"], [self.route])
        self.assertEqual(kwargs["user"], self.manager)
        self.assertTrue(kwargs["deduplicate"])
        self.assertIn(self.manager, kwargs["job_id"])

    def test_bulk_needs_create_permission_at_enqueue(self):
        with self.set_user(self.manager), patch(f"{API}.frappe.enqueue") as enqueue:
            with patch(f"{API}.frappe.has_permission", side_effect=frappe.PermissionError):
                with self.assertRaises(frappe.PermissionError):
                    bulk_convert_docs_pages([self.route], self.category)
        enqueue.assert_not_called()

    def test_bulk_queues_one_index_job_and_pauses_between_pages(self):
        with self.job_db(), patch("frappe.enqueue") as enqueue, patch(f"{CONVERT}.time.sleep") as sleep:
            run_bulk([self.route, self.other], self.category, self.manager)
        self.assertEqual(len(article_index_jobs(enqueue)), 1)
        self.assertEqual(sleep.call_count, 2)

    def test_a_failure_after_insert_leaves_no_row_and_can_be_retried(self):
        calls = []

        def boom(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise frappe.ValidationError("hook")

        with (
            self.job_db(),
            patch("frappe.enqueue"),
            patch(HOOK, side_effect=boom),
            patch(f"{CONVERT}.frappe.log_error") as log,
        ):
            run_bulk([self.route, self.other], self.category, self.manager)
            self.assertFalse(frappe.db.exists("HD Article", {"docs_page_route": self.route}))
            self.assertTrue(frappe.db.exists("HD Article", {"docs_page_route": self.other}))
            log.assert_called_once()  # a ValidationError after insert is unexpected
            run_bulk([self.route], self.category, self.manager)
        self.assertTrue(frappe.db.exists("HD Article", {"docs_page_route": self.route}))
        with self.set_user(self.manager):
            self.assertEqual(get_bulk_convert_result(), {"created": 1, "skipped": 0})

    def test_a_second_bulk_is_refused_while_one_runs(self):
        key = result_key(self.manager)
        frappe.cache.set_value(key, {"created": 1, "skipped": 0})
        self.addCleanup(frappe.cache.delete_value, key)
        with (
            self.set_user(self.manager),
            patch(f"{API}.is_job_enqueued", return_value=True),
            patch(f"{API}.frappe.enqueue") as enqueue,
        ):
            with self.assertRaisesRegex(frappe.ValidationError, "already running"):
                bulk_convert_docs_pages([self.route], self.category)
        enqueue.assert_not_called()
        self.assertEqual(frappe.cache.get_value(key), {"created": 1, "skipped": 0})

    def test_marking_pages_ignores_an_empty_route(self):
        make_article(docs_page_route=None)
        page = {"route": "", "title": "Whatever"}
        mark_pages([page])
        self.assertEqual((page["converted"], page["matching"]), (None, None))

    def test_a_timeout_in_a_bulk_run_does_not_trip_the_breaker(self):
        wiki = WikiSource("https://docs.example.com", [])
        timeout = DocsFetchError("Timed out", transient=True)
        with (
            patch(f"{CONVERT}.get_source", return_value=wiki),
            patch("helpdesk.docs_source.wiki.fetch", side_effect=timeout),
            patch("helpdesk.docs_source.fetch.fetch", side_effect=timeout),
            self.job_db(),
            patch(f"{CONVERT}.time.sleep"),
            patch(f"{CONVERT}.frappe.log_error") as log,
        ):
            run_bulk([self.route, self.other], self.category, self.manager)
        log.assert_called_once()  # the outage, once per run
        self.assertFalse(frappe.cache.get_value(DOWN_KEY))
        with self.set_user(self.manager):
            self.assertEqual(get_bulk_convert_result(), {"created": 0, "skipped": 2})

    def test_bulk_refuses_over_50_and_bad_category(self):
        routes = [f"a/{i}" for i in range(MAX_BULK + 1)]
        with self.set_user(self.manager), patch(f"{API}.frappe.enqueue") as enqueue:
            with self.assertRaises(frappe.ValidationError):
                bulk_convert_docs_pages(routes, self.category)
            bulk_convert_docs_pages(routes[:MAX_BULK], self.category)
            with self.assertRaises(frappe.DoesNotExistError):
                bulk_convert_docs_pages([self.route], "nope")
        enqueue.assert_called_once()

    def test_bulk_reports_created_and_skipped(self):
        self.convert(self.other)
        routes = [self.route, self.other, "helpdesk/missing"]
        with self.job_db() as commit, patch(f"{CONVERT}.frappe.log_error") as log:
            run_bulk(routes, self.category, self.manager)
        self.assertEqual(commit.call_count, 4)  # a page each, then the end
        log.assert_not_called()  # refusals are plain skips
        self.assertEqual(self.source.live_calls[1:], [False] * 3)  # [0] is the setup convert
        self.assertTrue(frappe.db.exists("HD Article", {"docs_page_route": self.route}))
        with self.set_user(self.manager):
            self.assertEqual(get_bulk_convert_result(), {"created": 1, "skipped": 2})
        with self.set_user(self.agent), self.assertRaises(frappe.PermissionError):
            get_bulk_convert_result()

    def test_one_failure_skips_only_that_page(self):
        original = self.source.get_page

        def broken(route, live=True):
            if route == self.other:
                raise RuntimeError("boom")
            return original(route)

        self.source.get_page = broken
        with self.job_db(), patch(f"{CONVERT}.frappe.log_error") as log:
            run_bulk([self.other, self.route], self.category, self.manager)
        log.assert_called_once()
        self.assertFalse(frappe.db.exists("HD Article", {"docs_page_route": self.other}))
        self.assertTrue(frappe.db.exists("HD Article", {"docs_page_route": self.route}))


class TestReaders(ConvertCase):
    def search_routes(self):
        return [r["route"] for r in search_docs("x")]

    def test_draft_keeps_docs_page_in_search_and_page_view(self):
        self.convert()
        with self.set_user(self.customer):
            self.assertEqual(self.search_routes(), [self.route])
            self.assertEqual(get_doc_page(self.route)["title"], self.title)

    def test_published_replaces_only_its_own_page(self):
        other = unique_name("Other")
        self.source.hits = [hit(self.route, self.title), hit(self.other, other)]
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        with self.set_user(self.customer):
            self.assertEqual(self.search_routes(), [self.other])

    def test_restricted_article_keeps_docs_page_for_those_who_cannot_read_it(self):
        article = self.convert()
        frappe.db.set_value("HD Article", article, {"status": "Published", "visibility": "Customers"})
        with change_settings("HD Settings", {"public_knowledge_base": 1}), self.set_user("Guest"):
            self.assertEqual(self.search_routes(), [self.route])
            self.assertEqual(get_doc_page(self.route)["title"], self.title)
        with self.set_user(self.customer):
            self.assertEqual(self.search_routes(), [])

    def test_archived_article_brings_docs_page_back(self):
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        frappe.db.set_value("HD Article", article, "status", "Archived")
        with self.set_user(self.customer):
            self.assertEqual(self.search_routes(), [self.route])

    def test_old_link_redirects_only_for_readers(self):
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        with self.set_user(self.customer):
            page = get_doc_page(self.route)
        self.assertEqual(set(page), {"article"})
        self.assertEqual(page["article"]["name"], article)
        self.assertEqual(page["article"]["title_slug"], frappe.website.utils.cleanup_page_name(self.title))
        frappe.db.set_value("HD Article", article, "visibility", "Private")
        with self.set_user(self.customer):
            self.assertIn("content", get_doc_page(self.route))

    def test_an_empty_route_matches_no_article(self):
        make_article(docs_page_route=None)
        self.assertIsNone(converted_article("/"))
        self.assertEqual(readable_converted_routes(["", "/"]), set())
        with self.set_user(self.customer), self.assertRaises(frappe.DoesNotExistError):
            get_doc_page("/")

    def test_redirect_needs_no_live_source(self):
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        self.source.get_page = lambda route, live=True: (_ for _ in ()).throw(DocsFetchError("down"))
        with patch(f"{API}.get_source", return_value=None), self.set_user(self.customer):
            self.assertEqual(get_doc_page(self.route)["article"]["name"], article)

    def test_redirect_follows_the_final_route(self):
        self.pages["old/path"] = {**self.pages[self.route], "route": self.route}
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        with self.set_user(self.customer):
            self.assertEqual(get_doc_page("old/path")["article"]["name"], article)

    def test_renamed_article_keeps_the_link(self):
        article = self.convert()
        frappe.db.set_value("HD Article", article, {"status": "Published", "title": unique_name("Renamed")})
        with self.set_user(self.customer):
            self.assertEqual(get_doc_page(self.route)["article"]["name"], article)

    def test_related_hides_a_converted_page_outside_related_articles(self):
        self.pages[f"{self.route}-two"] = {"title": "Two", "content": "<p>x</p>", "source_url": "u"}
        self.source.hits = [hit(self.route, "Gone"), hit(self.other, "Other")]
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        with self.set_user(self.customer):
            related = get_doc_page(f"{self.route}-two")["related"]
        self.assertEqual([d["route"] for d in related["docs"]], [self.other])

    def test_only_agents_get_converted_and_matching(self):
        match = make_article(self.title)
        article = self.convert()
        with self.set_user(self.agent):
            page = get_doc_page(self.route)
        self.assertEqual(page["converted"], {"name": article, "title": self.title})
        self.assertEqual(page["matching"], {"name": match, "title": self.title})
        for user in (self.customer, "Guest"):
            with change_settings("HD Settings", {"public_knowledge_base": 1}), self.set_user(user):
                page = get_doc_page(self.route)
            self.assertNotIn("converted", page)
            self.assertNotIn("matching", page)

    def test_get_article_shows_source_fields_to_agents_only(self):
        article = self.convert()
        frappe.db.set_value("HD Article", article, "status", "Published")
        with self.set_user(self.agent):
            data = get_article(article)
        self.assertEqual(data.docs_page_url, self.source_url)
        self.assertTrue(data.docs_copied_on)
        with self.set_user(self.customer):
            data = get_article(article)
        self.assertNotIn("docs_page_url", data)
        self.assertNotIn("docs_copied_on", data)


class TestListPages(ConvertCase):
    def test_marks_converted_and_matching(self):
        match = make_article(self.title)
        make_article(self.pages[self.other]["title"], status="Archived")
        article = self.convert()
        with self.set_user(self.agent):
            pages = {p["route"]: p for p in list_docs_pages("helpdesk")}
        self.assertEqual(pages[self.route]["converted"], {"name": article, "title": self.title})
        self.assertEqual(pages[self.route]["matching"], {"name": match, "title": self.title})
        other = pages[self.other]
        self.assertEqual((other["converted"], other["matching"]), (None, None))

    def test_customer_cannot_list(self):
        with self.set_user(self.customer), self.assertRaises(frappe.PermissionError):
            list_docs_pages()

    def test_listing_uses_a_fixed_number_of_queries(self):
        for i in range(10):
            self.pages[f"helpdesk/p{i}"] = {"title": f"P{i}", "content": "x", "source_url": "u"}
        with self.set_user(self.agent), patch(f"{CONVERT}.frappe.get_all", wraps=frappe.get_all) as get_all:
            list_docs_pages()
        self.assertEqual(get_all.call_count, 2)
