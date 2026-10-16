# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


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
        # Imported here: the API module imports the article controller, which imports this one.
        from helpdesk.api.knowledge_base import get_general_category

        if general_category := get_general_category():
            frappe.db.set_value(
                "HD Article",
                {"category": self.name},
                get_values_for_category(general_category),
                update_modified=False,
            )


def get_category_visibility(category: str) -> str | None:
    """The access every article in `category` the user can read shares; None when they differ."""
    values = frappe.get_list(
        "HD Article",
        filters={"category": category},
        pluck="visibility",
        distinct=True,
    )
    return values[0] if len(values) == 1 else None


def get_values_for_category(category: str) -> dict:
    """An article joining a category whose articles share one access takes it."""
    values = {"category": category}
    if visibility := get_category_visibility(category):
        values["visibility"] = visibility
    return values


def check_category_length(category: str | None) -> None:
    if category and frappe.db.count("HD Article", {"category": category}) == 1:
        frappe.throw(_("Category must have at least one article"))
