import frappe

@frappe.whitelist(allow_guest=True)
def get_all():
	all_agents = frappe.get_all("Agent", fields=['agent_name', 'name', 'team'])

	for agent in all_agents:
		user = frappe.get_doc("User", agent['name'])
		team = frappe.get_doc("Team", agent['team'])
		agent['user'] = user.__dict__
		agent['team'] = team.__dict__
		
		agent['roles'] = []
		for role in user.roles:
			agent['roles'].append(role.role)

	return all_agents


@frappe.whitelist(allow_guest=True)
def get_session_agent():
	session_user = frappe.session.user
	session_agent = None
	if session_user and frappe.db.exists("Agent", session_user):
		session_agent = frappe.get_doc("Agent", session_user)
		session_agent = session_agent.__dict__
		session_agent["image"] = frappe.get_value("User", session_user, "user_image")
	return session_agent

@frappe.whitelist(allow_guest=True)
def get_user():
	session_user = frappe.session.user
	session_agent = get_session_agent()
	return {
		'agent': session_agent,
		'profile_image': frappe.get_value("User", session_user, "user_image")
	}
	