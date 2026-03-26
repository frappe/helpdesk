import frappe
from frappe.desk.form.assign_to import add as add_assign

AUTHOR_EMAIl = "john@example.com"
AUTHOR_NAME = "John Doe"
CONTENT = """
<div style="font-family: 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.8; color: #374151; max-width: 560px; margin: 0 auto;">
Hi 👋
<br><br>
We thought we'd use this space to give you a quick walkthrough while you're here 🙂
<br><br>
This is a sample ticket we created so you can see how Frappe Helpdesk works.
<br><br>
Here's how to read this screen:<br>
<b>Center:</b> This is the ticket thread. All customer emails and replies show up here.<br>
<b>Reply:</b> Respond to the customer (sends an email)<br>
<b>Comment:</b> Internal notes for your team (not visible to customers)<br>
<br><br>
<img src="/assets/helpdesk/desk/demo1.gif" style="width: 100%; max-width: 560px; border-radius: 10px; margin: 16px 0; display: block;">
<br><br>
<b>Right side:</b> Manage the ticket — Assign to yourself or a teammate, Set priority, type, and customer, Update status<br>
<img src="/assets/helpdesk/desk/demo2.gif" style="width: 100%; max-width: 560px; border-radius: 10px; margin: 16px 0; display: block;">
<br><br>
<b>Top:</b> SLA tracking + source — First response and resolution timers, See where the ticket came from (email or portal)
<img src="/assets/helpdesk/desk/timers.png" style="width: 100%; max-width: 560px; border-radius: 10px; margin: 16px 0; display: block;">
<br><br>
What you can do next:<br>
<ul style="padding-left: 20px; margin: 0;">
  <li>Connect your support email to start receiving real tickets</li>
  <li>Invite your team and auto-assign tickets</li>
  <li>Set up SLAs to manage response times</li>
  <li>Add a Knowledge Base for self-serve support</li>
  <li>Enable the customer portal for ticket tracking</li>
</ul>
<br><br>
You can explore on your own, or just reply to this ticket to see how it works.
<br><br>
If you need help, reach out to us here: <a href="https://support.frappe.io/helpdesk" style="color: #3b82f6;">https://support.frappe.io/helpdesk</a>
<img src="/path/to/logo.png" alt="Frappe" style="width: 120px; display: block; margin-bottom: 12px;">
Best,<br>
Team Frappe
</div>
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
