# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDArticleCategory(Document):
    def validate(self):
        self.validate_default_category()

    def validate_default_category(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        old_value = old_doc.get("category_name")

        if self.has_value_changed("category_name") and old_value == "General":
            frappe.throw(_("General category name can't be changed"))

    def on_trash(self):
        if self.category_name == "General":
            frappe.throw(_("General category can't be deleted"))
            return

        articles = frappe.get_all(
            "HD Article", filters={"category": self.name}, pluck="name"
        )

        general_category = frappe.db.get_value(
            "HD Article Category", {"category_name": "General"}, "name"
        )
        if not general_category:
            return

        try:
            for article in articles:
                frappe.db.set_value("HD Article", article, "category", general_category)
        except Exception as e:
            frappe.db.rollback()
