# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.api.knowledge_base import get_general_category
from helpdesk.helpdesk.doctype.hd_article.hd_article import (
    get_joining_values,
    update_articles,
)


class HDArticleCategory(Document):
    def validate(self):
        self.validate_default_category()
        self.validate_general_category()

    def validate_general_category(self):
        if self.category_name.strip().lower() != "general":
            return

        if frappe.db.exists(
            "HD Article Category",
            {"category_name": "General", "name": ("!=", self.name)},
        ):
            frappe.throw(
                _(
                    "General is a reserved category name. Please use a different name to proceed.",
                    self.name,
                )
            )

    def validate_default_category(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        old_value = old_doc.get("category_name")

        if self.has_value_changed("category_name") and old_value == "General":
            frappe.throw(_("General category name can't be changed"))

    def on_trash(self):
        self.validate_general_category_delete()
        self.move_articles_to_general()

    def validate_general_category_delete(self):
        if self.category_name == "General":
            frappe.throw(_("General category can't be deleted"))

    def move_articles_to_general(self):
        if general_category := get_general_category():
            update_articles(
                {"category": self.name}, get_joining_values(general_category)
            )
