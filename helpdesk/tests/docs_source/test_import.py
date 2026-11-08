from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.knowledge_base import get_article
from helpdesk.docs_source import importer
from helpdesk.docs_source.fetch import DocsFetchError
from helpdesk.docs_source.importer import (
    DocsImport,
    DocsImportError,
    normalize_url,
    page_key,
)
from helpdesk.test_utils import (
    article_index_jobs,
    get_category_articles,
    make_article,
    make_article_category,
    make_docs_page,
    make_docs_site,
    patch_docs_site,
    unique_name,
)

HOST = "docs.example.com"
BASE = f"https://{HOST}"


class DocsImportCase(IntegrationTestCase):
    def setUp(self):
        self.enterContext(patch("frappe.db.commit"))
        self.addCleanup(frappe.db.rollback)
        self.category = make_article_category(unique_name("Imports")).name

    def run_import(self, url=BASE):
        return DocsImport(url, self.category).run()

    def articles(self):
        return get_category_articles(self.category)


class TestSources(DocsImportCase):
    def test_llms_first_then_sitemap(self):
        fetch = patch_docs_site(
            self, make_docs_site(HOST, {"a": "Alpha"}, llms=True, sitemap=True)
        )
        self.assertEqual(self.run_import()["created"], 1)
        urls = [call.args[0] for call in fetch.call_args_list]
        self.assertNotIn(f"{BASE}/sitemap.xml", urls)

    def test_html_llms_txt_falls_back_to_sitemap(self):
        site = make_docs_site(HOST, {"a": "Alpha"}, llms=False, sitemap=True)
        site[f"{BASE}/llms.txt"] = make_docs_page("Not found")
        patch_docs_site(self, site)
        self.assertEqual(self.run_import()["created"], 1)

    def test_llms_links_without_md_are_imported_as_html(self):
        site = {
            f"{BASE}/llms.txt": f"- [Guide]({BASE}/guide): about\n",
            f"{BASE}/guide": make_docs_page("Guide"),
            f"{BASE}/sitemap.xml": "<urlset><url><loc>https://docs.example.com/other</loc></url></urlset>",
        }
        fetch = patch_docs_site(self, site)
        self.assertEqual(self.run_import()["created"], 1)
        self.assertEqual([a.title for a in self.articles()], ["Guide"])
        self.assertNotIn(
            f"{BASE}/sitemap.xml", [c.args[0] for c in fetch.call_args_list]
        )

    def test_no_list_raises_nothing_found_copy(self):
        patch_docs_site(self, {})
        with self.assertRaises(DocsImportError) as caught:
            self.run_import()
        self.assertIn("llms.txt or sitemap.xml", str(caught.exception))
        self.assertIn(HOST, str(caught.exception))


class TestCreate(DocsImportCase):
    def test_creates_drafts_with_url_and_date(self):
        site = make_docs_site(HOST, {"a": "Alpha", "b/c": "x" * 300, "d": "Alpha"})
        patch_docs_site(self, site)
        with patch("frappe.enqueue") as enqueue:
            result = self.run_import()
        self.assertEqual(result, {"created": 3, "skipped": 0, "failed": 0})
        self.assertEqual(len(article_index_jobs(enqueue)), 1)
        rows = {row.docs_page_url: row for row in self.articles()}
        self.assertEqual(set(rows), {f"{BASE}/a", f"{BASE}/b/c", f"{BASE}/d"})
        for row in rows.values():
            self.assertEqual(row.status, "Draft")
            self.assertTrue(row.docs_copied_on)
        self.assertEqual(len(rows[f"{BASE}/b/c"].title), 140)

    def test_title_is_cleaned_once(self):
        site = make_docs_site(HOST, {"a": "Vec<T> basics", "b": "Fish &amp;amp; Chips"})
        patch_docs_site(self, site)
        importer_ = DocsImport(BASE, self.category)
        self.assertEqual(importer_.read_one(f"{BASE}/a.md")[0], "Vec<T> basics")
        self.assertEqual(importer_.read_one(f"{BASE}/b.md")[0], "Fish &amp; Chips")

    def test_second_run_skips_imported_and_adds_new(self):
        site = make_docs_site(HOST, {"a": "Alpha", "b": "Beta"})
        patch_docs_site(self, site)
        self.assertEqual(self.run_import()["created"], 2)

        patch_docs_site(
            self, make_docs_site(HOST, {"a": "Alpha", "b": "Beta", "c": "Gamma"})
        )
        result = self.run_import()

        self.assertEqual(result, {"created": 1, "skipped": 2, "failed": 0})
        self.assertEqual([a.title for a in self.articles()], ["Alpha", "Beta", "Gamma"])
        self.assertEqual(self.run_import(), {"created": 0, "skipped": 3, "failed": 0})

    def test_url_variants_are_one_page(self):
        self.assertEqual(
            {page_key(u) for u in (f"{BASE}/a/", f"{BASE}/a.md", f"{BASE}/a#x")},
            {f"{BASE}/a"},
        )
        site = {
            f"{BASE}/llms.txt": f"- [A]({BASE}/a.md)\n- [A again]({BASE}/a/)\n- [A]({BASE}/a#x)\n",
            f"{BASE}/a.md": "# A\n\nThe text of the first page.\n",
            f"{BASE}/a/": make_docs_page("A"),
        }
        patch_docs_site(self, site)
        self.assertEqual(self.run_import()["created"], 1)
        self.assertEqual(self.run_import()["created"], 0)

    def test_cap_counts_new_pages_only(self):
        pages = {f"p{i:02d}": f"Page {i:02d}" for i in range(45)}
        patch_docs_site(self, make_docs_site(HOST, pages))
        with patch.object(importer, "MAX_PAGES", 20):
            created = [self.run_import()["created"] for _ in range(4)]
        self.assertEqual(created, [20, 20, 5, 0])
        self.assertEqual(len(self.articles()), 45)

    def test_unreadable_page_counts_failed_and_rest_import(self):
        site = make_docs_site(
            HOST, {"a": "Alpha", "b": "Beta", "c": "Gamma", "d": "Delta"}
        )
        site[f"{BASE}/b.md"] = 500
        site[f"{BASE}/c.md"] = "No heading here, only some words."
        site[f"{BASE}/d.md"] = "# Delta\n\n"
        patch_docs_site(self, site)
        self.assertEqual(self.run_import(), {"created": 1, "skipped": 0, "failed": 3})
        self.assertEqual([a.title for a in self.articles()], ["Alpha"])

    def test_content_hash_stored_and_edit_detected(self):
        patch_docs_site(self, make_docs_site(HOST, {"a": "Alpha"}))
        self.run_import()
        name = self.articles()[0].name
        self.assertFalse(get_article(name).docs_edited)
        self.assertNotIn("docs_content_hash", get_article(name))

        frappe.db.set_value("HD Article", name, "content", "<p>Changed</p>")
        self.assertTrue(get_article(name).docs_edited)

        copy = frappe.copy_doc(frappe.get_doc("HD Article", name), ignore_no_copy=False)
        self.assertFalse(
            copy.docs_page_url or copy.docs_copied_on or copy.docs_content_hash
        )

        plain = make_article(category=self.category)
        self.assertFalse(get_article(plain).docs_edited)


class TestNormalize(IntegrationTestCase):
    def test_accepts_and_cleans_a_public_https_address(self):
        for raw, expected in [
            ("  https://Docs.Example.com/  ", BASE),
            ("https://docs.example.com/docs/?a=1#top", f"{BASE}/docs"),
            ("docs.example.com", BASE),
        ]:
            self.assertEqual(normalize_url(raw), expected, raw)

    def test_rejects_anything_else_with_plain_copy(self):
        for raw in [
            "",
            "http://docs.example.com",
            "https://user:pw@docs.example.com",
            "https://docs.example.com/" + "x" * 500,
            None,
        ]:
            with self.assertRaises(DocsImportError, msg=raw) as caught:
                normalize_url(raw)
            self.assertIn("https://", str(caught.exception))


class TestFriendlyMessages(DocsImportCase):
    def test_messages_never_leak_error_text(self):
        for error, expected in [
            (DocsFetchError("HTTP 403", status=403), "did not let us read"),
            (DocsFetchError("HTTP 503", status=503), "did not answer in time"),
            (DocsFetchError("Timed out", transient=True), "did not answer in time"),
            (DocsFetchError("10.0.0.1 is private"), "can't reach that address"),
            (DocsFetchError("HTTP 404", status=404), "couldn't find an llms.txt"),
        ]:
            with (
                patch("helpdesk.docs_source.llms.fetch", side_effect=error),
                patch("helpdesk.docs_source.sitemap.fetch", side_effect=error),
            ):
                with self.assertRaises(DocsImportError) as caught:
                    self.run_import()
            message = str(caught.exception)
            self.assertIn(expected, message, error)
            for leak in ("HTTP", "private", "Timed out", "server"):
                self.assertNotIn(leak, message)