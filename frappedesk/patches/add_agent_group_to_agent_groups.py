import frappe


def execute():
	frappe.reload_doc("FrappeDesk", "doctype", "Agent")
	frappe.reload_doc("FrappeDesk", "doctype", "Agent Group Item")
	frappe.reload_doc("FrappeDesk", "doctype", "Agent Group")
	frappe.reload_doc("FrappeDesk", "doctype", "Frappe Desk Settings")

	agents = frappe.get_all("Agent", pluck="name")
	for agent in agents:
		agent_doc = frappe.get_doc("Agent", agent)
		if agent_doc.group:
			group_item = frappe.get_doc(
				{"doctype": "Agent Group Item", "agent_group": agent_doc.group}
			)
			agent_doc.append("groups", group_item)
			agent_doc.save()
