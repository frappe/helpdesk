import time
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.docs_source import get_source
from helpdesk.docs_source.fetch import DocsFetchError
from helpdesk.docs_source.sitemap import MAX_PAGES, MIN_TEXT, SitemapSource, _locs
from helpdesk.test_utils import fake_docs_fetch, make_docs_page as page

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://{host}/docs/intro</loc>
    <lastmod>2026-01-02</lastmod>
    <changefreq>weekly</changefreq>
  </url>
  <url><loc>
    https://{host}/docs/guides/domain?a=1&amp;b=2
  </loc></url>
  <url><loc>https://{host}/blog/news</loc></url>
  <url><loc>https://other.example.org/docs/x</loc></url>
  <url><loc>https://{host}/docs/../secret</loc></url>
  <url><loc>http://[bad</loc></url>
</urlset>
"""
INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://{host}/sitemap-a.xml</loc><lastmod>2026-01-01</lastmod></sitemap>
  <sitemap><loc>https://{host}/sitemap-b.xml</loc></sitemap>
</sitemapindex>
"""
CHILD = """<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://{host}/docs/{name}</loc></url></urlset>
"""
TEXT = "Point your own domain at the site and verify the record. " * 6
DOCUSAURUS = f"""<!doctype html><html><head><title>Custom domain | Acme</title></head><body>
<div id="__docusaurus">
<nav class="navbar"><a href="/">Menu</a></nav>
<div class="docPage">
  <aside class="sidebar"><ul><li>Sidebar link</li></ul></aside>
  <main><div class="container"><article>
    <header><h1>Custom <b>domain</b></h1></header>
    <nav class="breadcrumbs">Breadcrumb</nav>
    <div class="theme-doc-toc-mobile">Mobile TOC</div><span class="theme-doc-version-badge">Version 3</span>
    <p>{TEXT}</p><script>alert(1)</script><style>p {{}}</style>
    <div><pre><code>npm start</code></pre><button type="button">Copy</button></div>
    <p>See <a href="/docs/intro">intro</a>.</p>
  </article></div>
  <div class="col col--3"><div class="tableOfContents"><ul><li>On this page TOC</li></ul></div></div>
  </main>
</div>
<footer>Copyright Acme</footer>
</div></body></html>"""


class TestSitemap(IntegrationTestCase):
    def setUp(self):
        self.host = f"docs-{frappe.generate_hash(length=6)}.example.com"
        self.url = f"https://{self.host}/docs"
        self.site = {f"https://{self.host}/sitemap.xml": SITEMAP.format(host=self.host)}
        self.source = SitemapSource(self.url)
        self.fetch = self.enterContext(
            patch("helpdesk.docs_source.sitemap.fetch", side_effect=self._fetch)
        )
        self.enterContext(
            patch("helpdesk.docs_source.indexed.fetch_live", side_effect=self._fetch)
        )
        self.sleep = self.enterContext(patch("helpdesk.docs_source.sitemap.time.sleep"))
        frappe.cache.delete_keys("helpdesk_docs_llms")
        self.addCleanup(frappe.cache.delete_keys, "helpdesk_docs_llms")

    def _fetch(self, *args, **kwargs):
        return fake_docs_fetch(self.site)(*args, **kwargs)

    def _add(self, path, html):
        self.site[f"https://{self.host}{path}"] = html

    def test_reads_sitemap_xml_and_skips_bad_locs(self):
        self._add("/docs/intro", page("Intro"))
        self._add("/docs/guides/domain?a=1&b=2", page("Domain"))
        label, pages = self.source.read_pages()
        self.assertEqual(label, self.host)
        self.assertEqual(
            [(p["route"], p["title"]) for p in pages],
            [("docs/intro", "Intro"), ("docs/guides/domain", "Domain")],
        )
        self.assertEqual(pages[1]["url"], f"https://{self.host}/docs/guides/domain?a=1&b=2")
        self.assertNotIn("<", pages[0]["body"])
        self.assertNotIn("  ", pages[0]["body"])
        self.assertFalse(self.source.truncated)

    def test_reads_sitemap_index_one_level(self):
        self.site[f"https://{self.host}/sitemap.xml"] = INDEX.format(host=self.host)
        for name in ("a", "b"):
            self._add(f"/sitemap-{name}.xml", CHILD.format(host=self.host, name=name))
            self._add(f"/docs/{name}", page(name.upper()))
        _, pages = self.source.read_pages()
        self.assertEqual([p["route"] for p in pages], ["docs/a", "docs/b"])

    def test_keeps_only_connected_path_and_host(self):
        urls = self.source._page_urls()
        self.assertEqual(
            urls,
            [
                f"https://{self.host}/docs/intro",
                f"https://{self.host}/docs/guides/domain?a=1&b=2",
            ],
        )

    def test_stops_at_1000_and_flags_truncated(self):
        locs = "".join(
            f"<url><loc>https://{self.host}/docs/p{i}</loc></url>" for i in range(MAX_PAGES + 5)
        )
        self.site[f"https://{self.host}/sitemap.xml"] = f"<urlset>{locs}</urlset>"
        with patch("helpdesk.docs_source.sitemap.fetch", side_effect=self._page_for_any):
            _, pages = self.source.read_pages()
        self.assertEqual(len(pages), MAX_PAGES)
        self.assertTrue(self.source.truncated)
        self.assertEqual(self.sleep.call_count, MAX_PAGES - 1)

    def _page_for_any(self, url, host, *args, **kwargs):
        if url.endswith("sitemap.xml"):
            return self._fetch(url, host)
        self.site[url] = page("P")
        return self._fetch(url, host)

    def test_main_drops_nav_and_footer(self):
        title, html = self.source.extract_main(DOCUSAURUS)
        self.assertEqual(title, "Custom domain")
        for gone in ("Menu", "Sidebar", "Breadcrumb", "On this page", "Mobile TOC", "Version 3", "Copy", "alert", "<h1", "<script"):
            self.assertNotIn(gone, html)
        self.assertIn("verify the record", html)

    def test_title_falls_back_to_title_tag_and_broken_html_is_tolerated(self):
        title, _ = self.source.extract_main(
            "<html><head><title>Only &amp; title</title></head><body><main><p>x</main>"
        )
        self.assertEqual(title, "Only & title")  # no h1 in main
        for html in ("", "<<<", None):
            self.assertEqual(self.source.extract_main(html), ("", ""))
        self.assertEqual(self.source.extract_main("<main><div></main></span>")[0], "")

    def test_no_main_or_article_skips_page(self):
        self._add("/docs/intro", "<html><body><div>%s</div></body></html>" % TEXT)
        self._add("/docs/guides/domain?a=1&b=2", page("Domain"))
        _, pages = self.source.read_pages()
        self.assertEqual([p["route"] for p in pages], ["docs/guides/domain"])

    def test_failed_pages_are_skipped_but_none_readable_raises(self):
        self._add("/docs/intro", page("Intro"))
        # The domain page 404s, the intro page is kept.
        _, pages = self.source.read_pages()
        self.assertEqual(len(pages), 1)
        del self.site[f"https://{self.host}/docs/intro"]
        with self.assertRaises(DocsFetchError):
            self.source.read_pages()

    def test_no_readable_text_is_not_available(self):
        self._add("/docs/intro", page("Intro", "short"))
        self.assertFalse(SitemapSource(self.url).is_available())
        self._add("/docs/intro", page("Intro", "x " * MIN_TEXT))
        self.assertTrue(SitemapSource(self.url).is_available())
        self.site.clear()
        self.assertFalse(SitemapSource(self.url).is_available())

    def test_page_is_read_live_and_sanitized(self):
        self._add("/docs/intro", DOCUSAURUS)
        page_ = {"url": f"https://{self.host}/docs/intro", "title": "Custom domain"}
        html = self.source._read_html(page_)
        self.assertIn("verify the record", html)
        self.assertNotIn("<script", html)
        self.site.clear()  # second read comes from the cache
        self.assertEqual(self.source._read_html(page_), html)
        gone = {"url": f"https://{self.host}/docs/gone", "title": "x"}
        with self.assertRaises(frappe.DoesNotExistError):
            self.source._read_html(gone)

    def test_get_source_returns_sitemap_source(self):
        with change_settings(
            "HD Settings", {"docs_source_url": self.url, "docs_source_type": "Sitemap"}
        ):
            frappe.clear_cache(doctype="HD Settings")
            self.assertIsInstance(get_source(), SitemapSource)

    def test_tries_sub_path_sitemap_then_host_root(self):
        root = self.site.pop(f"https://{self.host}/sitemap.xml")
        self.site[f"{self.url}/sitemap.xml"] = root
        self.assertEqual(len(self.source._page_urls()), 2)

    def test_index_cap_counts_only_in_scope_urls(self):
        self.site[f"https://{self.host}/sitemap.xml"] = INDEX.format(host=self.host)
        blog = "".join(f"<url><loc>https://{self.host}/blog/{i}</loc></url>" for i in range(2500))
        self._add("/sitemap-a.xml", f"<urlset>{blog}</urlset>")
        self._add("/sitemap-b.xml", "<urlset>%s</urlset>" % "".join(
            f"<url><loc>https://{self.host}/docs/d{i}</loc></url>" for i in range(50)))
        self.assertEqual(len(self.source._page_urls()), 50)

    def test_sphinx_permalink_and_nav_h1_stay_out(self):
        title, html = self.source.extract_main(
            '<main><nav><h1>Nav</h1></nav><h1>Quickstart<a class="headerlink" href="#q">\u00b6</a></h1>'
            '<h2>Step<a class="hash-link" href="#s">#</a></h2><p>Body</p></main>'
        )
        self.assertEqual(title, "Quickstart")
        self.assertNotIn("\u00b6", html)
        self.assertNotIn("#</a>", html)

    def test_article_beats_main_and_role_main_beats_main(self):
        _, html = self.source.extract_main(DOCUSAURUS)
        self.assertNotIn("TOC", html)
        _, html = self.source.extract_main(
            '<main>Wrapper</main><div role="main"><p>Real</p></div>'
        )
        self.assertIn("Real", html)
        self.assertNotIn("Wrapper", html)

    def test_aside_dropped_except_inside_article(self):
        _, html = self.source.extract_main("<main><aside>Side</aside><p>Text</p></main>")
        self.assertNotIn("Side", html)
        _, html = self.source.extract_main(
            "<article><aside>Callout</aside><p>Text</p></article>"
        )
        self.assertIn("Callout", html)

    def test_versioned_urls_sort_last_before_cap(self):
        locs = [f"https://{self.host}/docs/{v}/x" for v in ("2.x", "v3", "3.10.2", "next")]
        locs += [f"https://{self.host}/docs/installation", f"https://{self.host}/docs/guide/a"]
        self.site[f"https://{self.host}/sitemap.xml"] = "<urlset>%s</urlset>" % "".join(
            f"<url><loc>{u}</loc></url>" for u in locs
        )
        urls = self.source._page_urls()
        self.assertEqual(len(urls), 6)
        self.assertEqual([u.split("/")[4] for u in urls[:2]], ["installation", "guide"])

    def test_outage_keeps_old_index(self):
        self._add("/docs/intro", page("Intro"))
        self.site[f"https://{self.host}/sitemap.xml"] = "<urlset>%s</urlset>" % "".join(
            f"<url><loc>https://{self.host}/docs/p{i}</loc></url>" for i in range(3)
        )
        self._add("/docs/p0", page("P0"))
        with self.assertRaises(DocsFetchError):  # 2 of 3 failed
            self.source.read_pages()

    def test_is_available_stops_at_first_sitemap_with_urls(self):
        self.site[f"https://{self.host}/sitemap.xml"] = INDEX.format(host=self.host)
        self._add("/sitemap-a.xml", CHILD.format(host=self.host, name="a"))
        self._add("/docs/a", page("A", "x " * MIN_TEXT))
        self.assertTrue(self.source.is_available())
        requested = [c.args[0] for c in self.fetch.call_args_list]
        self.assertNotIn(f"https://{self.host}/sitemap-b.xml", requested)

    def test_same_route_with_trailing_slash_counts_once(self):
        self.site[f"https://{self.host}/sitemap.xml"] = (
            f"<urlset><url><loc>https://{self.host}/docs/x</loc></url>"
            f"<url><loc>https://{self.host}/docs/x/</loc></url></urlset>"
        )
        self.assertEqual(len(self.source._page_urls()), 1)

    def test_loc_scan_is_linear_on_unclosed_loc(self):
        started = time.monotonic()
        _locs("<loc>" + " " * 5_000_000 + "<")
        self.assertLess(time.monotonic() - started, 1)

    def test_sub_path_sitemap_without_loc_falls_through_to_host_root(self):
        self.site[f"{self.url}/sitemap.xml"] = "<html><body>SPA catch-all</body></html>"
        self.assertEqual(len(self.source._page_urls()), 2)
