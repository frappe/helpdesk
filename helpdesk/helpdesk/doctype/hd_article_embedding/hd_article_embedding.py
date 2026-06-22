import frappe
from frappe.model.document import Document


class HDArticleEmbedding(Document):
    # Lifecycle hooks — no inline logic
    def before_insert(self):
        self.set_article_title()

    def before_save(self):
        self.set_article_title()

    # Methods
    def set_article_title(self):
        if self.article:
            self.article_title = frappe.db.get_value(
                "HD Article", self.article, "title"
            )
