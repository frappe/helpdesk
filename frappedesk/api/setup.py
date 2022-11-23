import frappe
from frappedesk.frappedesk.doctype.ticket.ticket import create_communication_via_contact


@frappe.whitelist()
def initial_agent_setup():
	support_settings_doc = frappe.get_doc("Frappe Desk Settings", "Frappe Desk Settings")
	if frappe.db.count("Agent") == 0:
		agent_added = False
		users = frappe.get_all(
			"User", filters={"user_type": "System User"}, order_by="creation"
		)
		for user in users:
			if user.name != "Administrator":
				agent = frappe.new_doc("Agent")
				agent.user = user.name
				agent.insert()
				agent_added = True

		if not agent_added:
			frappe.throw("No user found to create agent")

	support_settings_doc.initial_agent_set = True
	support_settings_doc.save()


@frappe.whitelist()
def create_initial_demo_ticket():
	support_settings_doc = frappe.get_doc("Frappe Desk Settings", "Frappe Desk Settings")
	if frappe.db.count("Ticket") == 0:
		agent = frappe.get_last_doc("Agent")
		if agent:
			frappe.get_doc(
				{
					"doctype": "Contact",
					"first_name": "Harshit",
					"last_name": "Agrawal",
					"email_ids": [{"email_id": "harshit@frappe.io", "is_primary": 1}],
				}
			).insert()

			new_ticket_doc = frappe.new_doc("Ticket")
			new_ticket_doc.subject = "Welcome to Frappe Desk"
			new_ticket_doc.description = """
			<p>Hi 👋🏻</p>
			<p><br></p>
			<p>I'm glad you decided to try Frappe Desk! We're working hard to build a better way for teams to communicate and serve customers well. I'm excited to get started.</p>
			<p><br></p>
			<p>You can get started right away by setting up a support email. This will help you see what your support will look like with FrappeDesk!</p>
			<p><br></p>
			<p>Best,</p>
			<p>Harshit</p>
			<p>Frappe Desk | Frappe.</p>
			"""
			new_ticket_doc.raised_by = "harshit@frappe.io"
			new_ticket_doc.contact = "Harshit Agrawal"
			new_ticket_doc.via_customer_portal = True
			new_ticket_doc.insert()

			create_communication_via_contact(new_ticket_doc.name, new_ticket_doc.description)
	support_settings_doc.initial_demo_ticket_created = True
	support_settings_doc.save()
	return
