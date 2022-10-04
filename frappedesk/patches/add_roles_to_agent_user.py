import frappe


def execute():
	agents = frappe.get_all("Agent", fields=["user", "name"])
	for agent in agents:
		agent_doc = frappe.get_doc("Agent", agent)
		agent_doc.set_user_roles()
