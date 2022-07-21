import frappe
from frappedesk.frappedesk.doctype.ticket.ticket import create_communication_via_contact

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

@frappe.whitelist()
def initial_demo_ticket_created():
	support_settings_doc = frappe.get_doc("Support Settings", "Support Settings")
	if support_settings_doc.initial_demo_ticket_created:
		return    
	ticket_count = len(frappe.get_all("Ticket"))
	if ticket_count == 0:
		agent = frappe.get_last_doc("Agent")
		if agent:
			new_ticket_doc = frappe.new_doc("Ticket")
			new_ticket_doc.subject = "Demo Ticket"
			new_ticket_doc.description = "This is a demo ticket created by the initial setup script."
			new_ticket_doc.ticket_type = "Question"
			new_ticket_doc.priority = "Low"
			new_ticket_doc.raised_by = "Administrator"
			new_ticket_doc.via_customer_portal = True
			new_ticket_doc.insert()

			create_communication_via_contact(new_ticket_doc.name, new_ticket_doc.description)

			support_settings_doc.initial_demo_ticket_created = True
			support_settings_doc.save()
			return
	else:
		return