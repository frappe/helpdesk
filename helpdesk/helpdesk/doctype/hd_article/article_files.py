"""An article's files stay as readable as the article: only a Public article's are public."""

import re
from html import escape
from urllib.parse import quote, urlsplit

import frappe
from frappe.utils import cint, get_url

PRIVATE_PREFIX = "/private"


class ArticleFiles:
    def __init__(self, article, private: bool):
        self.article, self.private = article, cint(private)

    def sync_new_article(self):
        self.adopt_uploads()
        self.sync()
        self.article.db_set("content", self.article.content, update_modified=False)

    def sync(self):
        for file in frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "HD Article",
                "attached_to_name": self.article.name,
                "file_url": ["like", "/%"],
            },
            fields=["name", "file_name", "file_url", "is_private"],
        ):
            self.sync_file(file)

    def adopt_uploads(self):
        """The new article page uploads before the article has a name."""
        if "/files/" not in (self.article.content or ""):
            return
        for file in frappe.get_all(
            "File",
            filters={
                "owner": frappe.session.user,
                "attached_to_name": ["is", "not set"],
                "file_url": ["like", "/%"],
                "is_folder": 0,
            },
            fields=["name", "file_url"],
            order_by="creation desc",
            limit=500,
        ):
            if self.uses(file.file_url):
                frappe.db.set_value(
                    "File",
                    file.name,
                    {
                        "attached_to_doctype": "HD Article",
                        "attached_to_name": self.article.name,
                    },
                    update_modified=False,
                )

    def sync_file(self, file):
        file_url = file.file_url
        if self.should_move(file):
            file_url = move_file(file.name, self.private)
        self.replace(file.file_url, file_url)
        self.repoint_stale_url(file_url, file.file_name)

    def should_move(self, file) -> bool:
        """Widening never publishes a file the content doesn't show."""
        if file.is_private == self.private:
            return False
        return bool(self.private) or self.uses(file.file_url)

    def repoint_stale_url(self, file_url: str, file_name: str):
        """An editor opened before the move still holds the other URL."""
        stale_url = get_other_url(file_url, file_name)
        if self.uses(stale_url) and not frappe.db.exists(
            "File", {"file_url": stale_url}
        ):
            self.replace(stale_url, file_url)

    def uses(self, file_url: str) -> bool:
        return bool(get_url_pattern(file_url).search(self.article.content or ""))

    def replace(self, old_url: str, new_url: str):
        if old_url != new_url and self.article.content:
            self.article.content = replace_file_url(
                self.article.content, old_url, new_url
            )


def move_file(file_name: str, private: int) -> str:
    """Frappe moves it on save and doesn't touch the content. Returns its URL."""
    file = frappe.get_doc("File", file_name)
    file.is_private = private
    try:
        file.save(ignore_permissions=True)
    except FileNotFoundError:
        # nothing on disk to protect, so the article can still save
        frappe.clear_last_message()
        return frappe.db.get_value("File", file_name, "file_url")
    return file.file_url


def get_other_url(file_url: str, file_name: str) -> str:
    """By `file_name`, because a move renames the file when its name is taken."""
    prefix = "" if file_url.startswith(PRIVATE_PREFIX) else PRIVATE_PREFIX
    return f"{prefix}/files/{file_name}"


def replace_file_url(content: str, old_url: str, new_url: str) -> str:
    return get_url_pattern(old_url).sub(
        lambda match: f"{match['start']}{match['origin'] or ''}{quote(new_url)}",
        content,
    )


def get_url_pattern(file_url: str) -> re.Pattern:
    """`file_url` as a whole link of this site, as written in HTML: never a part of a longer one."""
    forms = {file_url, quote(file_url), escape(file_url, quote=False)}
    urls = "|".join(re.escape(form) for form in forms)
    host = re.escape(urlsplit(get_url()).netloc)
    return re.compile(
        rf"""(?P<start>["'(]|&quot;)(?P<origin>https?://{host})?(?:{urls})(?=["')?#]|&quot;)"""
    )
