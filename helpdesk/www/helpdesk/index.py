import frappe
from helpdesk import __version__
from frappe.utils.telemetry import capture
no_cache = 1


def get_context(context):
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.frappe_version = frappe.__version__
	context.helpdesk_version = __version__
	context.site_name = frappe.local.site
	frappe.db.commit()

	# telemetry
	if frappe.session.user != "Guest":
		capture("active_site", "helpdesk")
	return context

@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw("This method is only meant for developer mode")
	return get_boot()

def get_boot():
    return frappe._dict(
        {
            "frappe_version": frappe.__version__,
            "default_route": get_default_route(),
            "site_name": frappe.local.site,
            "read_only_mode": frappe.flags.read_only,
			"csrf_token": frappe.sessions.get_csrf_token()
        }
    )

def get_default_route():
    return "/helpdesk"

