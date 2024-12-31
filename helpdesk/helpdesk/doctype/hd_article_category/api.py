import frappe


@frappe.whitelist()
def get_subcategories(parent_category):
    sub_categories = frappe.get_all(
        "HD Article Category",
        filters={"parent_category": parent_category},
        fields=["name", "category_name", "icon", "description"],
    )
    for sub_category in sub_categories:
        sub_category["article_count"] = frappe.db.count(
            "HD Article", {"category": sub_category["name"]}
        )
    return sub_categories
