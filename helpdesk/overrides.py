import frappe


def on_assignment_rule_trash(doc, event):
	if not frappe.get_all(
		"Assignment Rule",
		filters={"document_type": "HD Ticket", "name": ["!=", doc.name]},
	):
		frappe.throw("There should atleast be 1 assignment rule for ticket")
