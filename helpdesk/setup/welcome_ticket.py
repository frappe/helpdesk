import frappe
from frappe.desk.form.assign_to import add as add_assign

AUTHOR_EMAIl = "sabu@frappe.io"
AUTHOR_NAME = "Sabu Siyad"
CONTENT = """
<p>
Hi 👋
<br><br>
I'm glad you decided to try Helpdesk! We're working hard to build a better way for teams
to communicate and serve customers well.
<br><br>
You can get started right away by setting up a support email. This will help you see what
your support will look like with Helpdesk!
<br><br>
If you face any issues, please reach out to us via <a href="https://frappedesk.com/helpdesk">
https://frappedesk.com/helpdesk</a>
<br><br>
Best,
<br>
Sabu Siyad | Frappe Helpdesk.
"""


def create_welcome_ticket():
	create_contact()
	create_ticket()


def create_ticket():
	if frappe.db.count("HD Ticket"):
		return

	d = frappe.new_doc("HD Ticket")
	d.subject = "Welcome to Helpdesk"
	d.description = CONTENT
	d.raised_by = AUTHOR_EMAIl
	d.contact = AUTHOR_NAME
	d.via_customer_portal = True
	d.insert()
	d.create_communication_via_contact(d.description)
	add_assign(
		{
			"doctype": "HD Ticket",
			"name": d.name,
			"assign_to": ["Administrator"],
		}
	)


def create_contact():
	frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": AUTHOR_NAME,
			"email_ids": [{"email_id": AUTHOR_EMAIl, "is_primary": 1}],
		}
	).insert()
