# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HDCannedResponse(Document):
    def default_list_data():

        columns = [
            {
                "label": "Title",
                "type": "Data",
                "key": "title",
                "width": "5rem",
            },
            {
                "label": "Message",
                "type": "Text Editor",
                "key": "message",
                "width": "25rem",
            },
            {
                "label": "Owner",
                "type": "Link",
                "key": "owner",
                "width": "5rem",
            },
            {
                "label": "Modified On",
                "type": "Datetime",
                "key": "modified",
                "width": "5rem",
            },
        ]
        rows = ["title", "message", "owner", "modified"]
        return {"columns": columns, "rows": rows}
