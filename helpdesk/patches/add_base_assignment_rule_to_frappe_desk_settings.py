import frappe


def execute():
	frappe.reload_doc("Helpdesk", "doctype", "Agent")
	frappe.reload_doc("Helpdesk", "doctype", "Agent Group Item")
	frappe.reload_doc("Helpdesk", "doctype", "Agent Group")
	frappe.reload_doc("Helpdesk", "doctype", "Helpdesk Settings")

	settings = frappe.get_doc("Helpdesk Settings")
	if not settings.base_support_rotation:
		if frappe.db.exists("Assignment Rule", "Support Rotation"):
			settings.base_support_rotation = "Support Rotation"
			settings.save()
		else:
			settings.create_base_support_rotation()
