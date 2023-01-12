import frappe


def execute():
	frappe.reload_doc("Helpdesk", "doctype", "Agent")
	frappe.reload_doc("Helpdesk", "doctype", "Agent Group Item")
	frappe.reload_doc("Helpdesk", "doctype", "Agent Group")
	frappe.reload_doc("Helpdesk", "doctype", "Helpdesk Settings")

	agent_groups = frappe.get_all("Agent Group", pluck="name")
	for agent_group in agent_groups:
		agent_group_doc = frappe.get_doc("Agent Group", agent_group)
		rules = frappe.get_all(
			"Assignment Rule",
			filters={
				"document_type": "Ticket",
				"assign_condition": f"status == 'Open' and agent_group == '{agent_group}'",
			},
			pluck="name",
		)
		if len(rules) > 0:
			agent_group_doc.assignment_rule = rules[0]
			agent_group_doc.save()
		else:
			agent_group_doc.create_assignment_rule()
