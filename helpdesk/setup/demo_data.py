import frappe
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
	create_communication_via_contact,
)

AUTHOR_EMAIl = "hello@frappedesk.com"
AUTHOR_NAME = "Frappe Helpdesk Team"
DEMO_TICKET_CONTENT = """
<p>Hi 👋</p>
<p><br></p>
<p>We're glad you decided to try Helpdesk! We're working hard to build a better way for teams to communicate and serve customers well. I'm excited to get started.</p>
<p><br></p>
<p>You can get started right away by setting up a support email. This will help you see what your support will look like with Frappe Helpdesk!</p>
<p><br></p>
<p>Best,</p>
<p>Helpdesk Team | Frappe.</p>
"""


def create_demo_data():
	create_team_contact()
	create_demo_ticket()


def create_demo_ticket():
	if frappe.db.count("HD Ticket"):
		return

	d = frappe.new_doc("HD Ticket")
	d.subject = "Welcome to Helpdesk"
	d.description = DEMO_TICKET_CONTENT
	d.raised_by = AUTHOR_EMAIl
	d.contact = AUTHOR_NAME
	d.via_customer_portal = True
	d.insert()

	create_communication_via_contact(d.name, d.description)


def create_team_contact():
	frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": AUTHOR_NAME,
			"email_ids": [{"email_id": AUTHOR_EMAIl, "is_primary": 1}],
		}
	).insert()
