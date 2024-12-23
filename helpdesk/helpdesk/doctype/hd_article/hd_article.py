# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.utils import cint


class HDArticle(Document):
    @staticmethod
    def get_list_filters(query):
        QBArticle = DocType("HD Article")
        QBCategory = DocType("HD Article Category")

        query = (
            query.where(QBArticle.status != "Archived")
            .left_join(QBCategory)
            .on(QBCategory.name == QBArticle.category)
            .select(QBCategory.category_name)
            .select(
                QBArticle.title,
                QBArticle.status,
                QBArticle.author,
                QBArticle.modified,
            )
        )

        return query

    def before_insert(self):
        self.author = frappe.session.user

    def before_save(self):
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

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Title",
                "type": "Data",
                "key": "title",
                "width": "17rem",
            },
            {
                "label": "Status",
                "type": "status",
                "key": "status",
                "width": "24rem",
            },
            {
                "label": "Author",
                "type": "Data",
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
        rows = [
            "name",
            "title",
            "category",
            "status",
            "author",
            "published_on",
            "modified",
        ]
        return {"columns": columns, "rows": rows}

    @frappe.whitelist()
    def set_feedback(self, value):
        # 0 empty, 1 like, 2 dislike
        user = frappe.session.user
        feedback = frappe.db.exists(
            "HD Article Feedback", {"user": user, "article": self.name}
        )
        if feedback:
            frappe.db.set_value("HD Article Feedback", feedback, "feedback", value)
            return

        frappe.new_doc(
            "HD Article Feedback", user=user, article=self.name, feedback=value
        ).insert()

    @property
    def title_slug(self) -> str:
        """
        Generate slug from article title.
        Example: "Introduction to Frappe Helpdesk" -> "introduction-to-frappe-helpdesk"

        :return: Generated slug
        """
        return self.title.lower().replace(" ", "-")

    def get_breadcrumbs(self):
        breadcrumbs = [{"name": self.name, "label": self.title}]
        current_category = frappe.get_doc("Category", self.category)
        breadcrumbs.append(
            {"name": current_category.name, "label": current_category.category_name}
        )
        while current_category.parent_category:
            current_category = frappe.get_doc(
                "Category", current_category.parent_category
            )
            breadcrumbs.append(
                {"name": current_category.name, "label": current_category.category_name}
            )
        return breadcrumbs[::-1]
