import frappe
from helpdesk.setup.install import add_system_preset_filters


def execute():
	frappe.reload_doc("FrappeDesk", "doctype", "FD Preset Filter")
	frappe.reload_doc("FrappeDesk", "doctype", "FD Preset Filter Item")

	add_system_preset_filters()
