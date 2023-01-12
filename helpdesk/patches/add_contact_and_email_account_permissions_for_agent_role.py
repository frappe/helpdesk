import frappe
from frappe.permissions import add_permission


def execute():
	if frappe.db.exists("Role", "Agent"):
		add_permission("Contact", "Agent", 0)
		add_permission("Email Account", "Agent", 0)
