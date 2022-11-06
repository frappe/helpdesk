import frappe


def execute():
	agents = frappe.get_all("Agent", pluck="name")
	for agent in agents:
		agent_doc = frappe.get_doc("Agent", agent)
		group_item = frappe.get_doc(
			{"doctype": "Agent Group Item", "agent_group": agent_doc.group}
		)
		agent_doc.append("groups", group_item)
		agent_doc.save()
