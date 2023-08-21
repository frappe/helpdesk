import frappe

from helpdesk import __version__

no_cache = 1


def get_context(context):
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.frappe_version = frappe.__version__
	context.helpdesk_version = __version__
	context.site_name = frappe.local.site
	frappe.db.commit()
