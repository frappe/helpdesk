# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe

# from frappe import _
from frappe.model.document import Document


class HDArticleCategory(Document):
    def validate(self):
        self.validate_default_category()

    def validate_default_category(self):
        if self.has_value_changed("category_name"):
            frappe.throw("General category name can't be changed")

    def on_trash(self):
        if self.category_name == "General":
            frappe.throw("General category can't be deleted")
            return

        articles = frappe.get_all(
            "HD Article", filters={"category": self.name}, pluck="name"
        )
        try:
            for article in articles:
                frappe.db.set_value("HD Article", article, "category", None)
        except Exception as e:
            frappe.db.rollback()
