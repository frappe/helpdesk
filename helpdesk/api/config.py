import frappe


@frappe.whitelist(allow_guest=True)
def get_config():
	brand_logo = frappe.db.get_single_value("HD Settings", "brand_logo")
	brand_favicon = frappe.db.get_single_value("HD Settings", "brand_favicon")
	helpdesk_name = frappe.db.get_single_value("HD Settings", "helpdesk_name")
	is_setup_complete = frappe.db.get_single_value("HD Settings", "setup_complete")
	suppress_default_email_toast = frappe.db.get_single_value(
		"HD Settings", "suppress_default_email_toast"
	)

	return {
		"brand_logo": brand_logo,
		"brand_favicon": brand_favicon,
		"helpdesk_name": helpdesk_name,
		"is_setup_complete": is_setup_complete,
		"suppress_default_email_toast": suppress_default_email_toast,
	}
