import re
from urllib.parse import urljoin, urlsplit

from frappe.utils import md_to_html

from helpdesk.docs_source import sitemap
from helpdesk.docs_source.fetch import (
    MAX_CANDIDATES,
    MAX_CHILDREN,
    DocsFetchError,
    fetch,
)
from helpdesk.docs_source.text import clean_html, clean_markdown, in_scope, text_title

LINE = re.compile(r"^\s*[-*] \[(.+?)\]\((\S+?)\)(?:: (.*))?$", re.M)
# Mintlify lists big sites as /_llms/<section>.txt.
CHILD_INDEX = re.compile(r"/llms\.txt$|/_llms/.+\.txt$")


def find_pages(url: str) -> list[str]:
    """Page links of the site's llms.txt, as listed, following its child indexes.
    Empty when the file has no links. Raises DocsFetchError when it can't be read."""
    pages, children = _parse(f"{url}/llms.txt", url)
    for child in children[:MAX_CHILDREN]:
        try:
            pages += _parse(child, url)[0]
        except DocsFetchError:
            continue
    return list(dict.fromkeys(pages))[:MAX_CANDIDATES]


def read_page(url: str) -> tuple[str, str]:
    """The title and safe HTML of a page: a .md link is Markdown, any other is HTML."""
    text = fetch(url, urlsplit(url).hostname).text
    if not urlsplit(url).path.endswith(".md"):
        return sitemap.extract_main(text)
    heading = re.search(r"^# (.+)$", text, re.M)
    title = text_title(heading[1]) if heading else ""
    return title, clean_html(md_to_html(clean_markdown(text, title)))


def _parse(url: str, base_url: str) -> tuple[list[str], list[str]]:
    """The page links and child index links of one llms.txt, in scope."""
    text = fetch(url, urlsplit(base_url).hostname).text
    pages, children = [], []
    for _name, link, _summary in LINE.findall(text):
        try:
            link = urljoin(url, link)
        except ValueError:
            continue
        if not in_scope(link, base_url):
            continue
        is_index = CHILD_INDEX.search(urlsplit(link).path)
        (children if is_index else pages).append(link)
    return pages, list(dict.fromkeys(children))
