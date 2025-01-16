# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe

# from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class HDArticleCategory(Document):
    def before_save(self):
        if self.idx == -1 and self.status == "Published":
            # index is only set if its not set already, this allows defining
            # index at the time of creation itself if not set the index is set
            # to the last index + 1, i.e. the category is added at the end
            self.idx = cint(
                frappe.db.count(
                    "HD Article Category", {"parent_category": self.parent_category}
                )
            )

    def on_trash(self):
        articles = frappe.get_all(
            "HD Article", filters={"category": self.name}, pluck="name"
        )
        try:
            for article in articles:
                frappe.db.set_value("HD Article", article, "category", None)
        except Exception as e:
            frappe.db.rollback()
