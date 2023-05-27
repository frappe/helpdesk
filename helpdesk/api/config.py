import frappe


@frappe.whitelist(allow_guest=True)
def get_config():
	settings = frappe.get_single("HD Settings")

	return {
		"brand_logo": settings.brand_logo,
		"brand_favicon": settings.brand_favicon,
		"helpdesk_name": settings.helpdesk_name,
		"is_setup_complete": settings.setup_complete,
		"skip_email_workflow": settings.skip_email_workflow,
	}
