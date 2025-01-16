import frappe

from helpdesk.consts import DEFAULT_ARTICLE_CATEGORY


def execute():
    default_category = frappe.db.exists(
        "HD Article Category", {"category_name": DEFAULT_ARTICLE_CATEGORY}
    )
    if not default_category:
        default_category = frappe.get_doc(
            {
                "doctype": "HD Article Category",
                "category_name": DEFAULT_ARTICLE_CATEGORY,
            }
        ).insert()
        default_category = default_category.get("name")

    articles = frappe.get_all("HD Article", filters={"category": ""}, pluck="name")
    for article in articles:
        frappe.db.set_value("HD Article", article, "category", default_category)
