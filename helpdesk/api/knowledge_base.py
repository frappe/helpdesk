import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import get_user_info_for_avatar

from helpdesk.utils import is_agent


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
    article = frappe.get_doc("HD Article", name).as_dict()

    if not is_agent() and article["status"] != "Published":
        frappe.throw(_("Access denied"), frappe.PermissionError)

    author = get_user_info_for_avatar(article["author"])
    feedback = (
        frappe.db.get_value(
            "HD Article Feedback",
            {"article": name, "user": frappe.session.user},
            "feedback",
        )
        or 0
    )

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
        "feedback": int(feedback),
    }

    return article


@frappe.whitelist()
def delete_articles(articles):
    for article in articles:
        frappe.delete_doc("HD Article", article)


@frappe.whitelist()
def create_category(title: str):
    category = frappe.new_doc("HD Article Category", category_name=title).insert()
    article = frappe.new_doc(
        "HD Article", title="New Article", category=category.name
    ).insert()
    return {"article": article.name, "category": category.name}


@frappe.whitelist()
def move_to_category(category, articles):
    for article in articles:
        try:
            article_category = frappe.db.get_value("HD Article", article, "category")
            category_existing_articles = frappe.db.count(
                "HD Article", {"category": article_category}
            )
            if category_existing_articles == 1:
                frappe.throw("Category must have atleast one article")
                return
            else:
                frappe.db.set_value("HD Article", article, "category", category)
        except Exception as e:
            frappe.db.rollback()
            frappe.throw("Error moving article to category")


@frappe.whitelist()
def get_categories():
    categories = frappe.get_all(
        "HD Article Category",
        fields=["name", "category_name", "modified"],
    )
    for c in categories:
        c["article_count"] = frappe.db.count(
            "HD Article", filters={"category": c.name, "status": "Published"}
        )

    categories.sort(key=lambda c: c["article_count"], reverse=True)
    categories = [c for c in categories if c["article_count"] > 0]
    return categories


@frappe.whitelist()
def get_category_articles(category):
    articles = frappe.get_all(
        "HD Article",
        filters={"category": category, "status": "Published"},
        fields=["name", "title", "published_on", "modified", "author", "content"],
    )
    for article in articles:
        article["author"] = get_user_info_for_avatar(article["author"])
        soup = BeautifulSoup(article["content"], "html.parser")
        article["content"] = str(soup.text)[:100]

    return articles


@frappe.whitelist()
def get_general_category():
    return frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )


@frappe.whitelist()
def get_category_title(category):
    return frappe.db.get_value("HD Article Category", category, "category_name")
