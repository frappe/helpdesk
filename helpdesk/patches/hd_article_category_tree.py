import frappe
from frappe.query_builder import Case
from frappe.query_builder.functions import Coalesce
from frappe.utils.nestedset import rebuild_tree


def execute():
    """Number the category tree; old sites carry `lft`/`rgt` of an older tree."""
    category = frappe.qb.DocType("HD Article Category")
    is_top_level = Coalesce(category.parent_article_category, "") == ""
    frappe.qb.update(category).set(
        category.is_group, Case().when(is_top_level, 1).else_(0)
    ).set(category.old_parent, category.parent_article_category).run()
    rebuild_tree("HD Article Category")
