# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import sbool
from frappe.utils.nestedset import NestedSet

from helpdesk.utils import is_agent


class HDArticleCategory(NestedSet):
    def validate(self):
        # a cleared parent comes in as "", which the tree reads as a parent
        self.parent_article_category = self.parent_article_category or None
        # one level: only a top-level category takes children
        self.is_group = 0 if self.parent_article_category else 1
        self.validate_default_category()
        self.validate_general_category()
        self.validate_parent()
        self.validate_old_parent()
        self.validate_pinned_order()

    def validate_parent(self):
        """One level only; a Subcategory is never pinned."""
        if not self.parent_article_category:
            return

        if self.parent_article_category == self.name:
            frappe.throw(_("A category cannot be its own parent"))
        if self.category_name == "General":
            frappe.throw(_("General cannot be a subcategory"))
        # row lock: serialises two saves that would otherwise nest each other
        if frappe.db.get_value(
            "HD Article Category",
            self.parent_article_category,
            "parent_article_category",
            for_update=True,
        ):
            frappe.throw(_("A subcategory cannot have subcategories"))
        if not self.is_new() and frappe.db.get_value(
            "HD Article Category",
            {"parent_article_category": self.name},
            for_update=True,
        ):
            frappe.throw(_("A category with subcategories cannot have a parent"))

        if not self.pinned:
            return
        if not self.is_new() and self.has_value_changed("parent_article_category"):
            self.pinned = 0
            self.flags.unpinned = True
        else:
            frappe.throw(_("A subcategory cannot be pinned"))

    def validate_old_parent(self):
        old_doc = self.get_doc_before_save()
        if old_doc and self.has_value_changed("parent_article_category"):
            validate_keeps_content(
                old_doc.parent_article_category, leaving_subcategory=self.name
            )

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

    def on_update(self):
        if not self.is_new() and self.has_value_changed("category_name"):
            # the index carries each article's category name
            index_articles(
                frappe.get_all(
                    "HD Article", filters={"category": self.name}, pluck="name"
                )
            )
        if self.parent_article_category and self.has_value_changed(
            "parent_article_category"
        ):
            self.narrow_to_parent()
        super().on_update()

    def narrow_to_parent(self):
        # the parent's branch already counts this category in: leave it out
        visibility = get_category_visibility(
            self.parent_article_category, exclude=self.name
        )
        with batched_article_index():
            narrow_category_articles(self.name, visibility)

    def on_trash(self):
        self.validate_general_category_delete()
        if self.parent_article_category:
            move_category_articles(self.name, self.parent_article_category)
            # its moved articles, if any, fill the parent
            validate_keeps_content(
                self.parent_article_category,
                leaving_subcategory=self.name,
                message=_("Delete the parent category instead"),
            )
        else:
            self.promote_subcategories()
            self.move_articles_to_general()
        super().on_trash()

    def validate_general_category_delete(self):
        if self.category_name == "General":
            frappe.throw(_("General category can't be deleted"))

    def promote_subcategories(self):
        # Frappe's link check runs after on_trash.
        # Their lft/rgt stay: once this category is gone they nest in no one
        frappe.db.set_value(
            "HD Article Category",
            {"parent_article_category": self.name},
            {"parent_article_category": None, "old_parent": None, "is_group": 1},
        )

    def move_articles_to_general(self):
        # local import: circular via the article controller
        from helpdesk.api.knowledge_base import get_general_category

        if general_category := get_general_category():
            move_category_articles(self.name, general_category)


@frappe.whitelist(methods=["POST"])
def add_node(
    category_name: str, parent: str | None = None, is_root: bool | str = False
) -> dict:
    """The Tree view's add, with the desk's starter article.

    Frappe's own would set `parent_hd_article_category`."""
    # local import: circular via the article controller
    from helpdesk.api.knowledge_base import create_category

    return create_category(category_name, parent=None if sbool(is_root) else parent)


@frappe.whitelist()
def get_tree_nodes(doctype: str, parent: str = "", **kwargs) -> list[dict]:
    """The Tree view's nodes, by category name; Frappe's sort by the hash name."""
    return frappe.get_list(
        "HD Article Category",
        filters={"parent_article_category": parent or ["is", "not set"]},
        fields=["name as value", "category_name as title", "is_group as expandable"],
        order_by="category_name asc",
    )


# local imports below: circular via the article controller
def permission_query(user: str | None = None) -> str | None:
    """A category is readable when one of its or its subcategories' articles is."""
    from helpdesk.helpdesk.doctype.hd_article.hd_article import (
        permission_query as article_permission_query,
    )

    if not (conditions := article_permission_query(user)):
        return None
    # one level deep, so no recursion
    return (
        "(`tabHD Article Category`.name in "
        f"(select `tabHD Article`.category from `tabHD Article` where {conditions})"
        " or `tabHD Article Category`.name in "
        "(select sub.parent_article_category from `tabHD Article Category` sub"
        " join `tabHD Article` on `tabHD Article`.category = sub.name"
        f" where {conditions}))"
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
            filters=make_article_filters(user, category=["in", get_branch(doc.name)]),
            limit=1,
        )
    )


def get_category_visibility(category: str, exclude: str | None = None) -> str | None:
    """Read across the category and its subcategories but `exclude`.

    None when the articles' visibilities differ.
    """
    # not just the ones the caller can read
    branch = [name for name in get_branch(category) if name != exclude]
    values = read_visibilities(
        frappe.get_all(
            "HD Article",
            filters={"category": ["in", branch]},
            fields=["visibility", "status"],
            distinct=True,
        )
    )
    return values.pop() if len(values) == 1 else None


def read_visibilities(rows: list[dict]) -> set[str]:
    """Of a branch's article rows: published ones decide, a branch of only drafts reads its drafts."""
    published = [row for row in rows if row.status == "Published"]
    return {row.visibility for row in published or rows}


def get_joining_visibility(category: str) -> str | None:
    """What an article joining `category` narrows to; an empty subcategory reads its parent."""
    visibility = get_category_visibility(category)
    if not visibility and (parent := get_parent(category)):
        visibility = get_category_visibility(parent)
    return visibility


def get_subcategories(category: str) -> list[str]:
    return frappe.get_all(
        "HD Article Category",
        filters={"parent_article_category": category},
        order_by="category_name asc",
        pluck="name",
    )


def get_branch(category: str) -> list[str]:
    return [category, *get_subcategories(category)]


def get_parent(category: str) -> str | None:
    return frappe.db.get_value(
        "HD Article Category", category, "parent_article_category"
    )


SEPARATOR = " \u203a "


def format_category_label(name: str, parent_name: str | None = None) -> str:
    """`<parent> › <name>` for a Subcategory, the plain name otherwise."""
    return f"{parent_name}{SEPARATOR}{name}" if parent_name else name


def get_category_labels(names: list[str]) -> dict[str, str]:
    """A top-level name maps to its category name, a Subcategory to `<parent> › <name>`."""
    return {
        row.name: format_category_label(row.category_name, row.parent_name)
        for row in frappe.get_all(
            "HD Article Category",
            filters={"name": ["in", names]},
            fields=[
                "name",
                "category_name",
                "parent_article_category.category_name as parent_name",
            ],
        )
    }


# joining a category narrows access, never widens it
VISIBILITY_ORDER = ("Private", "Customers", "Public")


def get_stricter_visibility(visibility: str, category_visibility: str | None) -> str:
    if not category_visibility:
        return visibility
    return min(visibility, category_visibility, key=VISIBILITY_ORDER.index)


def validate_keeps_content(
    category: str | None,
    leaving_article: str | None = None,
    leaving_subcategory: str | None = None,
    message: str | None = None,
) -> None:
    """A category keeps an article or a Subcategory besides the one leaving it."""
    if (
        not category
        # a branch being deleted may empty its categories
        or category in (frappe.flags.deleting_category or ())
        or frappe.db.exists(
            "HD Article", {"category": category, "name": ["!=", leaving_article or ""]}
        )
        or set(get_subcategories(category)) - {leaving_subcategory}
    ):
        return
    if not message:
        name = frappe.db.get_value("HD Article Category", category, "category_name")
        message = (
            _(
                "This is the only article in {0}. Move another article in first, or delete the category."
            )
            if leaving_article
            else _("{0} would be left empty. Move or add an article to it first")
        ).format(name)
    frappe.throw(message)


def move_category_articles(source: str, target: str) -> None:
    """Bulk move: per-article saves would refuse to empty `source`."""
    moved = frappe.get_all("HD Article", filters={"category": source}, pluck="name")
    if not moved:
        return
    with batched_article_index():
        # narrowed before the move, so only the moved articles are touched
        # `source` may be a subcategory of `target`: its articles must not count
        narrow_category_articles(
            source, get_category_visibility(target, exclude=source)
        )
        frappe.db.set_value(
            "HD Article",
            {"category": source},
            "category",
            target,
            update_modified=False,
        )
        index_articles(moved)


def narrow_category_articles(category: str, visibility: str | None) -> None:
    """Saves each article `visibility` narrows, for version history."""
    articles = frappe.get_all(
        "HD Article", filters={"category": category}, fields=["name", "visibility"]
    )
    for row in articles:
        stricter = get_stricter_visibility(row.visibility, visibility)
        if stricter != row.visibility:
            article = frappe.get_doc("HD Article", row.name)
            article.visibility = stricter
            article.save()


@contextmanager
def batched_article_index():
    """Article saves inside queue their search index updates as one job."""
    if frappe.flags.batch_article_index is not None:
        yield  # the outer batch sends the job
        return
    frappe.flags.batch_article_index = articles = []
    try:
        yield
    finally:
        frappe.flags.batch_article_index = None
    index_articles(articles)


def index_articles(articles: list[str], queue: str = "long") -> None:
    """One job: a job per article overloads the queue on a big category. Inside
    `batched_article_index`, the batch sends it."""
    if (batch := frappe.flags.batch_article_index) is not None:
        batch.extend(articles)
        return
    if articles:
        frappe.enqueue(
            "helpdesk.search.update_article_indexes",
            # a save in the batch and the bulk move may name the same article
            articles=list(dict.fromkeys(articles)),
            queue=queue,
            enqueue_after_commit=True,
        )
