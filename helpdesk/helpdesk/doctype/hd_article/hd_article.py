# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.reportview import get_filters_cond
from frappe.model.document import Document
from frappe.types.filter import Filters
from frappe.utils import cint, evaluate_filters
from frappe.website.utils import cleanup_page_name

from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    check_category_length,
    get_category_visibility,
)
from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES
from helpdesk.utils import capture_event, is_agent

PUBLIC = "Public"
CUSTOMERS = "Customers"
PRIVATE = "Private"
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
        self.inherit_category_visibility()

    def before_save(self):
        self.excerpt = get_excerpt(self.content)

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

    def inherit_category_visibility(self):
        if (
            self.visibility == CUSTOMERS
            and self.category
            and get_category_visibility(self.category) == PRIVATE
        ):
            self.visibility = PRIVATE

    def after_insert(self):
        count = frappe.db.count("HD Article")
        if count == 1:
            return
        capture_event("article_created")

    def on_update(self):
        self.update_search_index()

    def on_trash(self):
        check_category_length(self.category)
        self.update_search_index()

    def update_search_index(self):
        frappe.enqueue(
            "helpdesk.search.update_article_index",
            article=self.name,
            queue="short",
            enqueue_after_commit=True,
        )

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
        """0 none, 1 like, 2 dislike; guests are keyed by `visitor_id`."""
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
        # guests lack create permission; validate_voter is the gate
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
        """Display only; the server ignores the slug in URLs."""
        return cleanup_page_name(self.title)


def get_excerpt(html: str | None) -> str:
    """First paragraph only: headings and table cells would run into it."""
    soup = BeautifulSoup(html or "", "html.parser")
    paragraph = next((p for p in soup.find_all("p") if p.get_text(strip=True)), soup)
    return " ".join(paragraph.get_text().split())[:EXCERPT_LENGTH]


def can_view_article(user: str, article) -> bool:
    if is_agent(user):
        return True
    return evaluate_filters(
        article, Filters(make_article_filters(user), doctype="HD Article")
    )


def make_article_filters(user: str | None = None, **extra) -> dict:
    user = user or frappe.session.user
    filters = {"status": "Published", **extra}
    if not is_agent(user):
        filters["visibility"] = ["in", get_readable_visibilities(user)]
    return filters


def get_readable_visibilities(user: str) -> list[str]:
    """Other apps' signed-in users lack a customer role: Public only."""
    if set(CUSTOMER_ROLES) & set(frappe.get_roles(user)):
        return [PUBLIC, CUSTOMERS]
    return [PUBLIC]


def get_voter(visitor_id: str | None) -> dict | None:
    if frappe.session.user != "Guest":
        return {"user": frappe.session.user}
    return {"visitor_id": visitor_id} if visitor_id else None


def permission_query(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    if is_agent(user):
        return None
    conditions = get_filters_cond(
        "HD Article", make_article_filters(user), [], ignore_permissions=True
    )
    return conditions.removeprefix(" and ")


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
    """Writes fall through to role permissions."""
    if ptype in ("write", "create", "delete"):
        return True
    return can_view_article(user or frappe.session.user, doc)
