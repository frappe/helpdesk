import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.docs_source import get_import_result, get_page_limit, import_docs
from helpdesk.docs_import import page_key
from helpdesk.test_utils import (
    create_agent,
    get_category_articles,
    make_agent_manager,
    make_article_category,
    run_last_docs_import,
    serve_docs_site,
    unique_email,
    unique_name,
)

HOST = "docs.example.com"
URL = f"https://{HOST}"


class DocsImportCase(IntegrationTestCase):
    def setUp(self):
        frappe.db.savepoint("docs_import_test")
        self.addCleanup(frappe.db.rollback, save_point="docs_import_test")
        self.site = serve_docs_site(self, HOST, {"a": "Alpha", "b/c": "x" * 300})
        self.category = make_article_category(unique_name("Imports")).name
        self.manager = make_agent_manager()

    def import_site(self, url=URL, **category) -> dict:
        with self.set_user(self.manager):
            started = import_docs(url, **(category or {"category": self.category}))
            if started["state"] != "running":
                return started
            run_last_docs_import()
            return get_import_result()


class TestImportDocs(DocsImportCase):
    def test_pages_become_drafts_with_their_docs_address(self):
        result = self.import_site()

        self.assertEqual(
            {k: result[k] for k in ("state", "created", "skipped", "failed")},
            {"state": "done", "created": 2, "skipped": 0, "failed": 0},
        )
        rows = {row.docs_page_url: row for row in get_category_articles(self.category)}
        self.assertEqual(set(rows), {f"{URL}/a", f"{URL}/b/c"})
        for row in rows.values():
            self.assertEqual(row.status, "Draft")
            self.assertTrue(row.docs_copied_on)
        self.assertEqual(len(rows[f"{URL}/b/c"].title), 140)

    def test_a_second_import_skips_pages_already_imported(self):
        self.import_site()
        self.site.requested.clear()

        result = self.import_site()

        self.assertEqual((result["created"], result["skipped"]), (0, 2))
        self.assertNotIn(f"{URL}/a", self.site.requested)
        self.assertEqual(len(get_category_articles(self.category)), 2)

    def test_unreadable_pages_are_listed_with_the_reason(self):
        self.site.add(
            f"{URL}/llms.txt", f"- [A]({URL}/a)\n- [Gone]({URL}/gone)", "text/plain"
        )

        result = self.import_site()

        self.assertEqual(result["created"], 1)
        self.assertEqual(
            result["unreadable"], [{"url": f"{URL}/gone", "reason": "not_found"}]
        )

    def test_a_site_without_llms_txt_or_sitemap_is_an_error(self):
        self.site.add(f"{URL}/llms.txt", status=404)

        result = self.import_site()

        self.assertEqual(result["state"], "error")
        self.assertIn("llms.txt or sitemap.xml", result["message"])

    def test_a_robots_txt_over_the_size_limit_asks_to_raise_it(self):
        self.site.add(f"{URL}/robots.txt", "#" * 2048, "text/plain")

        with change_settings("Web Crawl Settings", {"max_robots_size": 1}):
            result = self.import_site()

        self.assertEqual(result["state"], "error")
        self.assertIn("Maximum robots.txt size", result["message"])

    def test_new_category_is_created_only_when_the_import_starts(self):
        name = unique_name("Docs Site")

        refused = self.import_site("http://docs.example.com", new_category=name)
        self.assertEqual(refused["state"], "error")
        self.assertFalse(
            frappe.db.exists("HD Article Category", {"category_name": name})
        )

        blocked = self.import_site("https://127.0.0.1", new_category=name)
        self.assertIn("can't reach", blocked["message"])
        self.assertFalse(
            frappe.db.exists("HD Article Category", {"category_name": name})
        )

        self.import_site(new_category=name)
        category = frappe.db.get_value("HD Article Category", {"category_name": name})
        self.assertEqual(len(get_category_articles(category)), 2)


class TestPageLimit(DocsImportCase):
    def test_an_import_reads_at_most_the_settings_cap(self):
        with change_settings("Web Crawl Settings", {"max_pages": 1}):
            with self.set_user(self.manager):
                self.assertEqual(get_page_limit(), 1)
            result = self.import_site()
        self.assertEqual(result["created"], 1)

        with change_settings("Web Crawl Settings", {"max_pages": 500}):
            with self.set_user(self.manager):
                self.assertEqual(get_page_limit(), 200)


class TestImportRefusals(DocsImportCase):
    def test_agents_and_guests_cannot_import(self):
        for user in (create_agent(unique_email("plain-agent")).name, "Guest"):
            with self.set_user(user):
                with self.assertRaises(frappe.PermissionError, msg=user):
                    import_docs(URL, self.category)
                with self.assertRaises(frappe.PermissionError, msg=user):
                    get_page_limit()
                with self.assertRaises(frappe.PermissionError, msg=user):
                    get_import_result()

    def test_bad_addresses_and_categories_are_refused(self):
        with self.set_user(self.manager):
            for url in ("http://docs.example.com", "https://user:pw@docs.example.com"):
                self.assertIn("https://", import_docs(url, self.category)["message"])
            for category in ("No such category", ["a"], None):
                with self.assertRaises(frappe.DoesNotExistError, msg=category):
                    import_docs(URL, category)

    def test_a_second_import_waits_for_the_running_one(self):
        with self.set_user(self.manager):
            self.assertEqual(import_docs(URL, self.category)["state"], "running")
            self.assertIn("already running", import_docs(URL, self.category)["message"])


class TestPageKey(IntegrationTestCase):
    def test_spellings_of_a_page_share_one_key(self):
        for url in (
            f"{URL}/a",
            f"{URL}/a/",
            f"{URL}/a.md",
            f"{URL}/a?x=1#top",
            "https://DOCS.example.com/a",
        ):
            self.assertEqual(page_key(url), f"{URL}/a", url)
