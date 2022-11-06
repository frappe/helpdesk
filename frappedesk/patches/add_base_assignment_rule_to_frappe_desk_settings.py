import frappe


def execute():
	settings = frappe.get_doc("Frappe Desk Settings")
	if not settings.base_support_rotation:
		if frappe.db.exists("Assignment Rule", "Support Rotation"):
			settings.base_support_rotation = "Support Rotation"
			settings.save()
		else:
			settings.create_base_support_rotation()
