from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.docs_source.fetch import DocsFetchError
from helpdesk.docs_source.wiki import WikiSource
from helpdesk.test_utils import fake_docs_fetch

URL = "https://docs.example.com"
API = f"{URL}/api/method/wiki.frappe_wiki.doctype.wiki_document"
SEARCH = f"{API}.search.search"
PAGE = f"{API}.wiki_document.get_page_data"
ROOT = f"""# Docs

## Spaces

- [ERPNext](https://docs.example.com/erpnext/llms.txt)
- [Erpnext v12 user manual en](https://docs.example.com/erpnext/v12/user/manual/en/llms.txt)
- [Helpdesk](https://docs.example.com/helpdesk/llms.txt)
- [Legal](https://docs.example.com/legal/llms.txt)
- [Wiki v2](https://docs.example.com/wiki-v2/llms.txt)
"""
HELPDESK_INDEX = """# Helpdesk

- **Intro**
  - [Setup \\- Guide](https://docs.example.com/helpdesk/setup.md)
  - [Install](https://docs.example.com/helpdesk/install.md)
"""


def hit(route):
    return {"route": route, "title": f"T {route}", "content": "<b>x</b>"}


class TestWikiSource(IntegrationTestCase):
    def setUp(self):
        frappe.cache.delete_keys("helpdesk_docs_wiki")
        self.site = {f"{URL}/llms.txt": ROOT}
        self.addCleanup(frappe.cache.delete_keys, "helpdesk_docs_wiki")

    def source(self, hidden=()):
        return WikiSource(URL, list(hidden))

    def run_with(self, call, site=None, **kw):
        site = {**self.site, **(site or {})}
        fake = fake_docs_fetch(site)
        with (
            patch("helpdesk.docs_source.wiki.fetch", fake),
            patch("helpdesk.docs_source.wiki.fetch_live", fake),
        ):
            return call(self.source(**kw))

    def search(self, routes, **kw):
        site = {SEARCH: {"message": {"results": [hit(r) for r in routes]}}}
        found = self.run_with(lambda s: s.search("q"), site, **kw)
        return [h["route"] for h in found]

    def page(self, content="<p>hi</p>", route="helpdesk/setup", extra=None, **kw):
        data = {
            "title": "Setup",
            "rendered_content": content,
            "last_updated": "2026-01-01",
        }
        site = {f"{PAGE}": {"message": data}, **(extra or {})}
        return self.run_with(lambda s: s.get_page(route), site, **kw)

    def test_old_versions_never_show(self):
        self.assertEqual(self.search(["erpnext/v12/x", "erpnext/x"]), ["erpnext/x"])

    def test_hidden_section_never_shows(self):
        self.assertEqual(
            self.search(["legal/x", "helpdesk/x"], hidden=["legal"]), ["helpdesk/x"]
        )

    def test_unlisted_section_never_shows(self):
        self.assertEqual(self.search(["jsdf/as", "helpdesk/x"]), ["helpdesk/x"])

    def test_wiki_v2_is_a_normal_section(self):
        self.assertEqual(self.search(["wiki-v2/x"]), ["wiki-v2/x"])

    def test_hit_is_escaped_and_labelled(self):
        site = {
            SEARCH: {
                "message": {
                    "results": [
                        {
                            "route": "helpdesk/x",
                            "title": "<img src=x><mark>a</mark>",
                            "content": "<script>",
                        }
                    ]
                }
            }
        }
        found = self.run_with(lambda s: s.search("q"), site)[0]
        self.assertEqual(found["title"], "&lt;img src=x&gt;<mark>a</mark>")
        self.assertNotIn("<script>", found["excerpt"])
        self.assertEqual(found["category_label"], "Helpdesk")

    def test_hidden_page_is_not_found(self):
        with self.assertRaises(frappe.DoesNotExistError):
            self.page(hidden=["helpdesk"])

    def test_page_fields(self):
        page = self.page()
        self.assertEqual(page["label"], "Helpdesk docs")
        self.assertEqual(page["source_url"], f"{URL}/helpdesk/setup")
        self.assertEqual(page["site_url"], f"{URL}/helpdesk")
        self.assertEqual(page["last_updated"], "2026-01-01")

    def test_moved_page_follows_redirect(self):
        moved = {
            f"{URL}/erpnext/old": ("<html>", f"{URL}/erpnext/stock"),
            PAGE: 404,
        }

        def fake(url, host, *a, params=None):
            if url == PAGE and params["route"] == "erpnext/stock":
                return fake_docs_fetch(
                    {
                        PAGE: {
                            "message": {
                                "title": "Stock",
                                "rendered_content": "<p>x</p>",
                                "last_updated": None,
                            }
                        }
                    }
                )(url, host)
            return fake_docs_fetch({**self.site, **moved})(url, host)

        with (
            patch("helpdesk.docs_source.wiki.fetch", fake),
            patch("helpdesk.docs_source.wiki.fetch_live", fake),
        ):
            page = self.source().get_page("erpnext/old")
        self.assertEqual(page["source_url"], f"{URL}/erpnext/stock")
        self.assertEqual(page["label"], "ERPNext docs")

    def test_moved_into_hidden_section_is_not_found(self):
        site = {PAGE: 500, f"{URL}/helpdesk/old": ("x", f"{URL}/legal/terms")}
        with self.assertRaises(frappe.DoesNotExistError):
            self.page(route="helpdesk/old", extra=site, hidden=["legal"])

    def test_outage_is_not_swallowed(self):
        with self.assertRaises(DocsFetchError):
            self.page(extra={PAGE: 503})

    def test_sections_come_from_llms_and_skip_old_versions(self):
        sections = self.run_with(lambda s: s.sections())
        self.assertEqual(
            [s["key"] for s in sections], ["erpnext", "helpdesk", "legal", "wiki-v2"]
        )
        self.assertEqual(sections[0]["title"], "ERPNext")

    def test_list_pages_reads_nested_section_llms(self):
        site = {f"{URL}/helpdesk/llms.txt": HELPDESK_INDEX}
        pages = self.run_with(lambda s: s.list_pages("helpdesk"), site)
        self.assertEqual(
            pages,
            [
                {
                    "route": "helpdesk/setup",
                    "title": "Setup - Guide",
                    "section": "helpdesk",
                },
                {
                    "route": "helpdesk/install",
                    "title": "Install",
                    "section": "helpdesk",
                },
            ],
        )

    def test_hidden_section_not_in_list_pages(self):
        site = {f"{URL}/{key}/llms.txt": "" for key in ("erpnext", "legal", "wiki-v2")}
        site[f"{URL}/helpdesk/llms.txt"] = HELPDESK_INDEX
        self.assertEqual(
            self.run_with(
                lambda s: s.list_pages("helpdesk"), site, hidden=["helpdesk"]
            ),
            [],
        )
        self.assertEqual(
            self.run_with(lambda s: s.list_pages(None), site, hidden=["helpdesk"]), []
        )

    def test_unsafe_markup_is_removed(self):
        html = '<a href="javascript:alert(1)" onclick="x()">a</a><script>x</script>'
        content = self.page(html)["content"]
        self.assertNotIn("script", content)
        self.assertNotIn("onclick", content)

    def test_phishing_markup_is_removed(self):
        html = '<form action="https://evil.com"><input type="password"><button>Go</button></form><p>ok</p>'
        content = self.page(html)["content"]
        for tag in ("form", "input", "button"):
            self.assertNotIn(f"<{tag}", content)

    def test_broken_html_is_still_sanitized(self):
        content = self.page("<img src=x onerror=alert(1)//")["content"]
        self.assertNotIn("onerror", content)

    def test_bad_body_is_a_fetch_error(self):
        with self.assertRaises(DocsFetchError):
            self.run_with(lambda s: s.search("q"), {SEARCH: "<html>nope</html>"})
        with self.assertRaises(DocsFetchError):
            self.page(extra={PAGE: "<html>nope</html>"})
        with self.assertRaises(DocsFetchError):
            self.page(extra={PAGE: {"message": {"title": "x"}}})

    def test_malformed_message_is_a_fetch_error(self):
        for message in ({}, [], "x", None):
            frappe.cache.delete_keys("helpdesk_docs_wiki")
            with self.assertRaises(DocsFetchError):
                self.run_with(lambda s: s.search("q"), {SEARCH: {"message": message}})

    def test_is_available_is_false_for_a_null_message(self):
        site = {SEARCH: {"message": None}}
        self.assertFalse(self.run_with(lambda s: s.is_available(), site))
        site = {SEARCH: {"message": {"results": []}}}
        self.assertTrue(self.run_with(lambda s: s.is_available(), site))

    def test_is_available_needs_a_section(self):
        search = {SEARCH: {"message": {"results": []}}}
        for root in (404, "# Docs with no sections\n"):
            frappe.cache.delete_keys("helpdesk_docs_wiki")
            site = {**search, f"{URL}/llms.txt": root}
            self.assertFalse(self.run_with(lambda s: s.is_available(), site))

    def test_titles_from_llms_keep_angle_brackets(self):
        self.site[f"{URL}/llms.txt"] = "- [Vec\\<T\\> guide](/rust/llms.txt)\n"
        self.assertEqual(
            self.run_with(lambda s: s.sections()),
            [{"key": "rust", "title": "Vec<T> guide"}],
        )

    def test_links_in_code_text_are_not_rewritten(self):
        html = '<code>&lt;a href="/helpdesk/setup"&gt;</code><p data-href="/helpdesk/x">p</p>'
        content = self.page(html)["content"]
        self.assertNotIn("/help/articles", content)
        self.assertIn('&lt;a href="/helpdesk/setup"&gt;', content)

    def test_dot_segments_are_not_pages(self):
        with self.assertRaises(frappe.DoesNotExistError):
            self.page(route="helpdesk/%2e%2e/%2e%2e/api/method/x")
        html = '<a href="/helpdesk/%2e%2e/%2e%2e/api/method/x">a</a><a href="/helpdesk/../x">b</a>'
        self.assertNotIn("/help/articles", self.page(html)["content"])

    def test_md_links_point_at_articles_route(self):
        html = '<a href="/helpdesk/install.md#top">a</a>'
        self.assertIn(
            'href="/help/articles/helpdesk/install#top"', self.page(html)["content"]
        )

    def test_title_is_plain(self):
        site = {
            PAGE: {
                "message": {"title": "A &amp; <b>B</b>", "rendered_content": "<p>x</p>"}
            }
        }
        self.assertEqual(
            self.run_with(lambda s: s.get_page("helpdesk/setup"), site)["title"],
            "A & B",
        )

    def test_section_list_uses_the_live_fetch(self):
        def sync(*a, **k):
            raise AssertionError("sections must not use the sync fetch")

        with (
            patch("helpdesk.docs_source.wiki.fetch", sync),
            patch("helpdesk.docs_source.wiki.fetch_live", fake_docs_fetch(self.site)),
        ):
            self.assertTrue(self.source().sections())
        frappe.cache.delete_keys("helpdesk_docs_wiki")
        with patch(
            "helpdesk.docs_source.wiki.fetch_live",
            fake_docs_fetch({f"{URL}/llms.txt": 503}),
        ):
            with self.assertRaises(DocsFetchError):
                self.source().sections()

    def test_internal_links_point_at_articles_route(self):
        html = (
            '<a href="/helpdesk/setup#a">a</a><a href="/legal/x">b</a>'
            '<a href="https://other.com/y">c</a><img src="/files/i.png">'
        )
        content = self.page(html, hidden=["legal"])["content"]
        self.assertIn('href="/help/articles/helpdesk/setup#a"', content)
        self.assertIn(f'href="{URL}/legal/x"', content)
        self.assertIn('href="https://other.com/y"', content)
        self.assertIn(f'src="{URL}/files/i.png"', content)
