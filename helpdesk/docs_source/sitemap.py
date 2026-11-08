import re
from html import unescape
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from helpdesk.docs_source.fetch import (
    MAX_CANDIDATES,
    MAX_CHILDREN,
    DocsFetchError,
    fetch,
)
from helpdesk.docs_source.text import clean_html, in_scope, text_title

LOC = re.compile(r"<loc>([^<]*)</loc>")
VERSION = re.compile(r"^(v?\d+(\.(\d+|x))*|next)$")
MAIN = ("article", "[role=main]", "main")
COPY_BUTTONS = (
    'button[aria-label*="copy" i], button[title*="copy" i], button[class*="copy" i], '
    'button.clean-btn, button:-soup-contains("Copy")'
)
NOISE = f"nav, header, footer, script, style, {COPY_BUTTONS}, .theme-doc-toc-mobile, .theme-doc-version-badge"
PERMALINKS = "a.headerlink, a.hash-link"


def find_pages(url: str) -> list[str]:
    """In-scope page URLs of the site's sitemap.xml, unversioned first, following a
    sitemap index one level. Empty when there is no sitemap. Raises DocsFetchError
    when it can't be read."""
    host = urlsplit(url).hostname
    text = _read_root(url, host)
    if text is None:
        return []
    locs = _locs(text)
    if "<sitemapindex" in text:
        children = [loc for loc in locs if _host_of(loc) == host][:MAX_CHILDREN]
        locs = []
        for child in children:
            try:
                locs += _locs(fetch(child, host).text)
            except DocsFetchError:
                continue
    pages = list(dict.fromkeys(loc for loc in locs if in_scope(loc, url)))
    pages.sort(key=lambda page: _is_versioned(urlsplit(page).path))
    return pages[:MAX_CANDIDATES]


def read_page(url: str) -> tuple[str, str]:
    """The title and safe HTML of a page's main content."""
    return extract_main(fetch(url, urlsplit(url).hostname).text)


def extract_main(html: str) -> tuple[str, str]:
    """The title and sanitized main content of a page; empty when it has none."""
    soup = BeautifulSoup(html or "", "html.parser")
    main = next((m for sel in MAIN if (m := soup.select_one(sel))), None)
    if main is None:
        return "", ""
    for tag in main.select(PERMALINKS):
        tag.decompose()
    # Starlight callouts are asides, so an article keeps them.
    noise = NOISE if main.name == "article" else f"{NOISE}, aside"
    for tag in main.select(noise):
        # Docusaurus puts the page h1 in a header.
        if tag.parent is not None and not (tag.name == "header" and tag.find("h1")):
            tag.decompose()
    heading = main.find("h1") or soup.find("title")
    title = text_title(heading.get_text()) if heading else ""
    if heading is not None and heading.name == "h1":
        heading.decompose()
    return title, clean_html(str(main))


def _read_root(url: str, host: str) -> str | None:
    """The first sitemap.xml with links, under the path and then at the host root."""
    error = None
    for root in dict.fromkeys([f"{url}/sitemap.xml", f"https://{host}/sitemap.xml"]):
        try:
            text = fetch(root, host).text
        except DocsFetchError as e:
            error = e
            continue
        if "<loc>" in text:
            return text
    if error:
        raise error
    return None


def _host_of(loc: str) -> str | None:
    try:
        return urlsplit(loc).hostname
    except ValueError:
        return None


def _locs(text: str) -> list[str]:
    text = text.replace("<![CDATA[", "").replace("]]>", "")
    return [unescape(loc.strip()) for loc in LOC.findall(text)]


def _is_versioned(path: str) -> bool:
    return any(VERSION.match(part) for part in path.split("/"))
