import frappe
from frappedesk.setup.install import add_system_preset_filters


def execute():
	frappe.reload_doc("FrappeDesk", "FD Preset Filter")
	frappe.reload_doc("FrappeDesk", "FD Preset Filter Item")

	add_system_preset_filters()
