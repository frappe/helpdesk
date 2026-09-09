# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class HDTicketComment(Document):
    """Superseded by core Comment. The table survives the migration so the old
    rows stay readable; nothing writes it anymore."""
