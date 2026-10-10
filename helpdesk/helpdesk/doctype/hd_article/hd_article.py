# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.reportview import get_filters_cond
from frappe.model.document import Document
from frappe.types.filter import Filters
from frappe.utils import cint, evaluate_filters

from helpdesk.utils import capture_event, is_agent

PUBLIC = "Public"
CUSTOMERS_ONLY = "Customers only"
AGENTS_ONLY = "Agents only"
# What a list row shows of the body.
EXCERPT_LENGTH = 140


class HDArticle(Document):
    def validate(self):
        self.validate_article_category()
        self.validate_published_content()

    def validate_article_category(self):
        if self.has_value_changed("category") and not self.is_new():
            check_category_length(self.get_doc_before_save().get("category"))

    def validate_published_content(self):
        if self.status == "Published" and not self.content:
            frappe.throw(_("Published articles must have content."))

    def before_insert(self):
        self.author = frappe.session.user
        self.set_category_visibility()

    def before_save(self):
        self.set_excerpt()

        # set published date of the hd_article
        if self.status == "Published" and not self.published_on:
            self.published_on = frappe.utils.now()
        elif self.status == "Draft" and self.published_on:
            self.published_on = None

        if self.status == "Archived" and self.category != None:
            self.category = None

        # index is only set if its not set already, this allows defining index
        # at the time of creation itself if not set the index is set to the
        # last index + 1, i.e. the hd_article is added at the end
        if self.status == "Published" and self.idx == -1:
            self.idx = cint(
                frappe.db.count(
                    "HD Article",
                    {"category": self.category, "status": "Published"},
                )
            )

    def set_category_visibility(self):
        # Public is also the default, so an insert takes the category's shared access over it.
        if self.visibility == PUBLIC and self.category:
            self.visibility = get_shared_visibility(self.category) or PUBLIC

    def set_excerpt(self):
        self.excerpt = get_excerpt(self.content)

    def after_insert(self):
        count = frappe.db.count("HD Article")
        if count == 1:
            return
        capture_event("article_created")

    def on_trash(self):
        check_category_length(self.category)

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Title",
                "type": "Data",
                "key": "title",
                "width": "20rem",
            },
            {
                "label": "Status",
                "type": "status",
                "key": "status",
                "width": "10rem",
            },
            {
                "label": "Visibility",
                "type": "Select",
                "key": "visibility",
                "width": "10rem",
            },
            {
                "label": "Author",
                "type": "Link",
                "key": "author",
                "width": "17rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]
        return {"columns": columns}

    def set_feedback(self, value: int, visitor_id: str | None = None):
        """Record one vote: 0 none, 1 like, 2 dislike; a guest's is kept by `visitor_id`."""
        value = cint(value)
        if value not in (0, 1, 2):
            frappe.throw(_("Invalid vote"))
        self.validate_voter(visitor_id)
        self.save_feedback(get_voter(visitor_id), value)

    def validate_voter(self, visitor_id: str | None):
        if frappe.session.user != "Guest":
            return
        if not frappe.db.get_single_value(
            "HD Settings", "allow_anonymous_article_voting"
        ):
            frappe.throw(_("Voting requires an account"), frappe.PermissionError)
        if not visitor_id:
            frappe.throw(_("Please enable cookies to vote"))

    def save_feedback(self, voter: dict, value: int):
        feedback = frappe.db.exists(
            "HD Article Feedback", {**voter, "article": self.name}
        )
        if feedback:
            frappe.db.set_value("HD Article Feedback", feedback, "feedback", value)
            return
        # A guest holds no create permission; `validate_voter` is the gate.
        frappe.get_doc(
            {
                "doctype": "HD Article Feedback",
                "article": self.name,
                "feedback": value,
                **voter,
            }
        ).insert(ignore_permissions=True)

    @property
    def title_slug(self) -> str:
        """
        Generate slug from article title.
        Example: "Introduction to Frappe Helpdesk" -> "introduction-to-frappe-helpdesk"

        :return: Generated slug
        """
        return self.title.lower().replace(" ", "-")


def get_excerpt(html: str | None) -> str:
    """The first paragraph, read as a sentence: headings and table cells would run into it."""
    soup = BeautifulSoup(html or "", "html.parser")
    paragraph = next((p for p in soup.find_all("p") if p.get_text(strip=True)), soup)
    return " ".join(paragraph.get_text().split())[:EXCERPT_LENGTH]


def readable_audiences(user: str | None = None) -> list[str] | None:
    """The audiences `user` may read; `None` for an agent, who reads them all."""
    user = user or frappe.session.user
    if is_agent(user):
        return None
    if user == "Guest":
        return [PUBLIC]
    return [PUBLIC, CUSTOMERS_ONLY]


def readable_filters(user: str | None = None, **extra) -> dict:
    """Published articles in the user's audiences, as filters: the one rule for who reads what."""
    filters = {"status": "Published", **extra}
    audiences = readable_audiences(user)
    if audiences is not None:
        filters["visibility"] = ["in", audiences]
    return filters


def is_readable(article, user: str | None = None) -> bool:
    """The same rule for one article already fetched; an agent reads drafts too."""
    if readable_audiences(user) is None:
        return True
    return evaluate_filters(
        article, Filters(readable_filters(user), doctype="HD Article")
    )


def get_shared_visibility(category: str) -> str | None:
    """The access every article in `category` the user can read shares; None when they differ."""
    values = frappe.get_list(
        "HD Article",
        filters={"category": category},
        pluck="visibility",
        distinct=True,
    )
    return values[0] if len(values) == 1 else None


def get_joining_values(category: str) -> dict:
    """An article joining a category whose articles share one access takes it."""
    values = {"category": category}
    if visibility := get_shared_visibility(category):
        values["visibility"] = visibility
    return values


def update_articles(filters: dict, values: dict) -> None:
    """Bulk `set_value` skips the hook that reindexes, so this reindexes what it touched."""
    # search_sqlite imports this module
    from helpdesk.search_sqlite import reindex_articles

    names = frappe.get_all("HD Article", filters=filters, pluck="name")
    if not names:
        return
    frappe.db.set_value("HD Article", filters, values, update_modified=False)
    reindex_articles(names)


def check_category_length(category: str | None) -> None:
    if category and frappe.db.count("HD Article", {"category": category}) == 1:
        frappe.throw(_("Category must have at least one article"))


def get_voter(visitor_id: str | None) -> dict | None:
    """Who a vote belongs to: the user, or a guest by cookie; None for a guest without one."""
    if frappe.session.user != "Guest":
        return {"user": frappe.session.user}
    return {"visitor_id": visitor_id} if visitor_id else None


def permission_query(user: str | None = None) -> str | None:
    """Non-agents list only the published articles in their audiences, as on the portal."""
    if readable_audiences(user) is None:
        return None
    conditions = get_filters_cond(
        "HD Article", readable_filters(user), [], ignore_permissions=True
    )
    return conditions.removeprefix(" and ")


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
    """Gates whatever shows the article; writing it is left to role permissions."""
    if ptype in ("write", "create", "delete"):
        return True
    return is_readable(doc, user)
