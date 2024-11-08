# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

ADD_TO_GROUP_ACTION = {
	"fields": [
		{"fieldtype": "select", "label": "Group", "fieldname": "group"},
		{"fieldtype": "select", "label": "Type", "fieldname": "type"},
	]
}

# [
#   {
#     "action": "Add to group",
#     "payload": {
#       "group": "Business",
#       "type": "Round Robin"
#     }
#   }
# ]



class HDAutomation(Document):
	def apply(self, doc, event):
		if doc.doctype == "HD Ticket":
			pass


def apply_automations(doc, event):
	automations = frappe.db.get_all(
		"HD Automation",
		{"enabled": 1, "event": ("in", ["On ticket creation", "On ticket update"])},
	)
	for automation in automations:
		automation.apply(doc, event)
