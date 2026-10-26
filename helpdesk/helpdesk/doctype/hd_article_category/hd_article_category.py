# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import is_agent


class HDArticleCategory(Document):
    def validate(self):
        self.validate_default_category()
        self.validate_general_category()
        self.validate_pinned_order()

    def validate_pinned_order(self):
        """Order is 1-based; 0 means unpinned."""
        if not self.pinned:
            self.pinned_order = 0
        elif self.pinned_order < 1:
            frappe.throw(_("Pinned order must be 1 or more"))

    def validate_general_category(self):
        if self.category_name.strip().lower() != "general":
            return

        if frappe.db.exists(
            "HD Article Category",
            {"category_name": "General", "name": ("!=", self.name)},
        ):
            frappe.throw(
                _(
                    "General is a reserved category name. Please use a different name to proceed.",
                    self.name,
                )
            )

    def validate_default_category(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        old_value = old_doc.get("category_name")

        if self.has_value_changed("category_name") and old_value == "General":
            frappe.throw(_("General category name can't be changed"))

    def on_trash(self):
        self.validate_general_category_delete()
        self.move_articles_to_general()

    def validate_general_category_delete(self):
        if self.category_name == "General":
            frappe.throw(_("General category can't be deleted"))

    def move_articles_to_general(self):
        # local import: circular via the article controller
        from helpdesk.api.knowledge_base import get_general_category

        if general_category := get_general_category():
            move_category_articles(self.name, general_category)


# local imports below: circular via the article controller
def permission_query(user: str | None = None) -> str | None:
    """A category is readable when one of its articles is."""
    from helpdesk.helpdesk.doctype.hd_article.hd_article import (
        permission_query as article_permission_query,
    )

    if not (conditions := article_permission_query(user)):
        return None
    return (
        "`tabHD Article Category`.name in "
        f"(select `tabHD Article`.category from `tabHD Article` where {conditions})"
    )


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
    """Writes fall through to role permissions."""
    from helpdesk.helpdesk.doctype.hd_article.hd_article import make_article_filters

    user = user or frappe.session.user
    if ptype in ("write", "create", "delete") or is_agent(user):
        return True
    return bool(
        frappe.get_all(
            "HD Article",
            filters=make_article_filters(user, category=doc.name),
            limit=1,
        )
    )


def get_category_visibility(category: str) -> str | None:
    """None when the articles' visibilities differ."""
    # every article, not just the ones the caller can read
    values = frappe.get_all(
        "HD Article",
        filters={"category": category},
        pluck="visibility",
        distinct=True,
    )
    return values[0] if len(values) == 1 else None


# joining a category narrows access, never widens it
VISIBILITY_ORDER = ("Private", "Customers", "Public")


def get_stricter_visibility(visibility: str, category_visibility: str | None) -> str:
    if not category_visibility:
        return visibility
    return min(visibility, category_visibility, key=VISIBILITY_ORDER.index)


def move_category_articles(source: str, target: str) -> None:
    """Bulk move: per-article saves would refuse to empty `source`."""
    category_visibility = get_category_visibility(target)
    articles = frappe.get_all("HD Article", filters={"category": source}, pluck="name")
    frappe.db.set_value(
        "HD Article",
        {"category": source},
        "category",
        target,
        update_modified=False,
    )
    for name in articles:
        article = frappe.get_doc("HD Article", name)
        visibility = get_stricter_visibility(article.visibility, category_visibility)
        if visibility != article.visibility:
            article.visibility = visibility
            article.save()


def check_category_length(category: str | None) -> None:
    if category and frappe.db.count("HD Article", {"category": category}) == 1:
        frappe.throw(_("Category must have at least one article"))
