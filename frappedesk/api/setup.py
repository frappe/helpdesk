import frappe

@frappe.whitelist()
def initial_agent_setup():
	support_settings_doc = frappe.get_doc("Support Settings", "Support Settings")
	if support_settings_doc.initial_agent_set:
		return
	users = frappe.get_all("User", filters={"user_type": "System User"}, order_by="creation")
	for user in users:
		if user.name != "Administrator":
			agent = frappe.new_doc("Agent")
			agent.user = user.name
			agent.insert()
			support_settings_doc.initial_agent_set = True
			support_settings_doc.save()
			return