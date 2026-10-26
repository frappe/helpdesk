import re

from bs4 import BeautifulSoup, NavigableString, Tag

MARKS = {
    "strong": "*",
    "b": "*",
    "em": "_",
    "i": "_",
    "s": "~",
    "del": "~",
    "strike": "~",
    "code": "`",
}
BLOCKS = {
    "p",
    "div",
    "ul",
    "ol",
    "blockquote",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}


def html_to_whatsapp(html: str | None) -> str:
    """Turn editor HTML into WhatsApp text: *bold*, _italic_, ~strike~, `code` and bullets."""
    text = to_text(BeautifulSoup(html or "", "html.parser"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def to_text(node: Tag | NavigableString) -> str:
    if isinstance(node, NavigableString):
        return str(node)
    inner = "".join(to_text(child) for child in node.children)
    if node.name in MARKS:
        return wrap(inner, MARKS[node.name])
    if node.name == "br":
        return "\n"
    if node.name == "a":
        return node.get("href") or inner
    if node.name == "li":
        return f"• {inner.strip()}\n"
    if node.name in BLOCKS:
        return f"{inner.rstrip()}\n"
    return inner


def wrap(text: str, mark: str) -> str:
    # WhatsApp only formats when the marks touch the text, so spaces stay outside
    lead, body, trail = re.match(r"(\s*)(.*?)(\s*)$", text, re.DOTALL).groups()
    return f"{lead}{mark}{body}{mark}{trail}" if body else text
