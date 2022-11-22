import frappe


def execute():
	# Disable the base support rotation rule if no agents are active
	base_support_rotation_rule = frappe.get_doc(
		"Frappe Desk Settings"
	).get_base_support_rotation()
	if frappe.db.count("Agent", {"is_active": 1}) == 0:
		base_support_rotation_rule_doc = frappe.get_doc(
			"Assignment Rule", base_support_rotation_rule
		)
		base_support_rotation_rule_doc.disabled = 1
		base_support_rotation_rule_doc.save(ignore_permissions=True)

	# Disable the group support rotation rule, if no agents are active in an agent group
	# Get all agent group docs
	all_agent_groups = frappe.get_all(
		"Agent Group", fields=["name"], limit_page_length=9999
	)
	all_agent_group_docs = [
		frappe.get_doc("Agent Group", group.name) for group in all_agent_groups
	]

	# Check if for each agent group, there are active agents, if not, disable the group support rotation rule
	for agent_group_doc in all_agent_group_docs:
		# Get the group support rotation rule
		agent_group_assigmnent_rule_doc = frappe.get_doc(
			"Assignment Rule", agent_group_doc.get_assignment_rule()
		)
		# filter out agnets that are not active and has the current agent group in the agent group list
		filters = [
			["Agent Group Item", "agent_group", "=", agent_group_doc.name],
			["Agent", "is_active", "=", 1],
		]
		if frappe.db.count("Agent", filters=filters) == 0:
			agent_group_assigmnent_rule_doc.disabled = 1
		else:
			agent_group_assigmnent_rule_doc.disabled = 0
		agent_group_assigmnent_rule_doc.save(ignore_permissions=True)
