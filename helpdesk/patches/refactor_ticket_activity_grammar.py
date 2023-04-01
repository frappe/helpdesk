import frappe


def execute():
	activities = frappe.get_all("Ticket Activity", pluck="name")
	for activity in activities:
		a_doc = frappe.get_doc("Ticket Activity", activity)
		if "Create" in a_doc.action:
			a_doc.action = "created"
		else:
			a_doc.action = a_doc.action[0].lower() + a_doc.action[1:]
		a_doc.save()
