import re
from html import unescape
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from frappe.utils import strip_html_tags
from frappe.utils.html_utils import sanitize_html


def plain_title(title: str) -> str:
    """A title without markup, entities or llms.txt backslash escapes."""
    return unescape(strip_html_tags(title)).replace("\\", "").strip()


def text_title(title: str) -> str:
    """plain_title for a title that is not HTML, so `Vec<T>` keeps its `<T>`."""
    return plain_title(title.replace("<", "&lt;"))


NO_TAGS = (
    "form",
    "input",
    "button",
    "select",
    "textarea",
    "meta",
    "link",
    "html",
    "head",
    "body",
)


def clean_html(html: str) -> str:
    """The one sanitizer for fetched docs: no scripts, forms or document tags."""
    return sanitize_html(html, always_sanitize=True, disallowed_tags=NO_TAGS)


def has_dot_segment(route: str) -> bool:
    return any(part in (".", "..") for part in unquote(route).split("/"))


def absolute_links(html: str, base_url: str) -> str:
    """Make links and image sources absolute, so a copied page still points at the docs site."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("a[href], [src]"):
        for attr in ("href", "src"):
            value = tag.get(attr)
            if value is None or (attr == "href" and tag.name != "a"):
                continue
            if value.startswith("#") or re.match(
                r"[a-z][a-z0-9+.-]*:(?!//)", value, re.I
            ):
                continue
            tag[attr] = urljoin(base_url, value)
    return str(soup)


def clean_markdown(text: str, title: str) -> str:
    """A page for readers: no agent section, leading quote, GitBook tags or repeated title."""
    text = text.split("\n# Agent Instructions")[0]
    text = re.sub(r"\A(?:> .*\n)+", "", _strip_gitbook_tags(text).lstrip())
    text = re.sub(r"^> \[!\w+\]$", ">", text, flags=re.M)  # GitHub alert markers
    return re.sub(rf"\A\s*# {re.escape(title)}\s*\n", "", text)


def _strip_gitbook_tags(text: str) -> str:
    # GitBook's own block tags
    return re.sub(r"^\s*\{%.*?%\}\s*$", "", text, flags=re.M)
