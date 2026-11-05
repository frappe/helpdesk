import re
from collections.abc import Callable
from html import unescape
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup
from frappe.utils import strip_html_tags
from frappe.utils.html_utils import sanitize_html

ARTICLES = "/help/articles"


def plain_title(title: str) -> str:
    """A title without markup, entities or llms.txt backslash escapes."""
    return unescape(strip_html_tags(title)).replace("\\", "").strip()


NO_TAGS = ("form", "input", "button", "select", "textarea", "meta", "link", "html", "head", "body")


def clean_html(html: str) -> str:
    """The one sanitizer for fetched docs: no scripts, forms or document tags."""
    return sanitize_html(html, always_sanitize=True, disallowed_tags=NO_TAGS)


def has_dot_segment(route: str) -> bool:
    return any(part in (".", "..") for part in unquote(route).split("/"))


def rewrite_links(html: str, base_url: str, is_page: Callable[[str], bool]) -> str:
    """Point links to docs pages at the help center, and make the rest absolute."""
    host = urlsplit(base_url).netloc
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("a[href], [src]"):
        for attr in ("href", "src"):
            value = tag.get(attr)
            if value is None or (attr == "href" and tag.name != "a"):
                continue
            if value.startswith("#") or re.match(r"[a-z][a-z0-9+.-]*:(?!//)", value, re.I):
                continue
            parts = urlsplit(urljoin(base_url, value))
            route = parts.path.strip("/")
            if attr == "href" and parts.netloc == host and is_page(route):
                anchor = f"#{parts.fragment}" if parts.fragment else ""
                tag[attr] = f"{ARTICLES}/{route}{anchor}"
            else:
                tag[attr] = parts.geturl()
    return str(soup)
