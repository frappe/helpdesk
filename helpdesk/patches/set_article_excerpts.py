import frappe

from helpdesk.helpdesk.doctype.hd_article.hd_article import get_excerpt


def execute():
    for article in frappe.get_all("HD Article", fields=["name", "content"]):
        frappe.db.set_value(
            "HD Article",
            article.name,
            "excerpt",
            get_excerpt(article.content),
            update_modified=False,
        )
