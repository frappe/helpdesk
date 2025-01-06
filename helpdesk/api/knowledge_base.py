import frappe
from frappe import _
from frappe.utils import get_user_info_for_avatar

from helpdesk.utils import is_agent


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
    article = frappe.get_doc("HD Article", name).as_dict()

    if not is_agent() and article["status"] != "Published":
        frappe.throw(_("Access denied"), frappe.PermissionError)

    author = get_user_info_for_avatar(article["author"])

    return {
        "name": article.name,
        "title": article.title,
        "content": article.content,
        "author": author,
        "creation": article.creation,
        "status": article.status,
        "published_on": article.published_on,
        "modified": article.modified,
        "category_name": frappe.db.get_value(
            "HD Article Category", article.category, "category_name"
        ),
        "category_id": article.category,
    }

    return article


@frappe.whitelist()
def delete_category(name: str):
    print("\n\n", name, "\n\n")
    pass
