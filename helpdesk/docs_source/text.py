import re
from collections.abc import Callable
from html import unescape
from urllib.parse import urljoin, urlsplit

from frappe.utils import strip_html_tags

ARTICLES = "/help/articles"
ATTR = re.compile(r'\b(href|src)="([^"]*)"')


def plain_title(title: str) -> str:
    """A title without markup, entities or llms.txt backslash escapes."""
    return unescape(strip_html_tags(title)).replace("\\", "").strip()


def rewrite_links(html: str, base_url: str, is_page: Callable[[str], bool]) -> str:
    """Point links to docs pages at the help center, and make the rest absolute."""
    host = urlsplit(base_url).netloc

    def rewrite(match: re.Match) -> str:
        attr, value = match.groups()
        if value.startswith("#") or re.match(r"[a-z][a-z0-9+.-]*:(?!//)", value, re.I):
            return match[0]
        absolute = urljoin(base_url, value)
        parts = urlsplit(absolute)
        route = parts.path.strip("/")
        if attr == "href" and parts.netloc == host and is_page(route):
            anchor = f"#{parts.fragment}" if parts.fragment else ""
            return f'href="{ARTICLES}/{route}{anchor}"'
        return f'{attr}="{absolute}"'

    return ATTR.sub(rewrite, html)
