import frappe


@frappe.whitelist()
def is_enabled():
    return bool(
        frappe.get_system_settings("enable_telemetry")
        and frappe.conf.get("posthog_host")
        and frappe.conf.get("posthog_project_id")
    )


@frappe.whitelist()
def get_credentials():
    return {
        "project_id": frappe.conf.get("posthog_project_id"),
        "telemetry_host": frappe.conf.get("posthog_host"),
    }
