import frappe
from frappe import _

from helpdesk.utils import is_agent


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
    article = frappe.get_doc("HD Article", name).as_dict()

    if not is_agent() and article["status"] != "Published":
        frappe.throw(_("Access denied"), frappe.PermissionError)

    author = frappe.get_cached_doc("User", article["author"])
    sub_category = frappe.get_cached_doc("HD Article Category", article["category"])
    category = frappe.get_cached_doc(
        "HD Article Category", sub_category.parent_category or article["category"]
    )

    user = frappe.session.user
    # TODO: views count increment with views field in HD Article
    # if not is_agent() and user != author.name:
    # frappe.db.set_value("HD Article", name, "views", article["views"] + 1)

    feedback = {
        "user_feedback": frappe.db.get_value(
            "HD Article Feedback", {"user": user, "article": name}, "feedback"
        )
        or None,
        "total_likes": frappe.db.count(
            "HD Article Feedback", {"article": name, "feedback": "Like"}
        ),
        "total_dislikes": frappe.db.count(
            "HD Article Feedback", {"article": name, "feedback": "Dislike"}
        ),
    }

    return {
        **article,
        "author": author,
        "category": category,
        "sub_category": sub_category,
        "feedback": feedback,
    }
