# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HDCustomer(Document):
    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Name",
                "key": "name",
                "width": "30rem",
                "type": "Data",
            },
            {
                "label": "Domain",
                "key": "domain",
                "width": "30rem",
                "type": "Data",
            },
            {
                "label": "Created On",
                "key": "creation",
                "width": "20rem",
                "type": "Datetime",
            },
        ]
        rows = [
            "name",
            "image",
            "domain",
            "modified",
            "creation",
        ]
        return {"columns": columns, "rows": rows}
