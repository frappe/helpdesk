import frappe


@frappe.whitelist()
def get_config():
	helpdesk_name = frappe.db.get_single_value("HD Settings", "helpdesk_name")
	suppress_default_email_toast = frappe.db.get_single_value(
		"HD Settings", "suppress_default_email_toast"
	)

	return {
		"helpdesk_name": helpdesk_name,
		"suppress_default_email_toast": suppress_default_email_toast,
	}
