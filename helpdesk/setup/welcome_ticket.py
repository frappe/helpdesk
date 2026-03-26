import frappe
from frappe.desk.form.assign_to import add as add_assign

AUTHOR_EMAIl = "john@example.com"
AUTHOR_NAME = "John Doe"
CONTENT = """
<div style="font-family: 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.8; color: #374151; max-width: 560px; margin: 0 auto;">
Hey {{user.first_name}} 👋,
<br><br>
We thought we'd use this space to give you a quick walkthrough while you're here 🙂
<br><br>
This is a sample ticket we created so you can see how Frappe Helpdesk works.
<br>
Getting started is simple. In the main <b>Ticket activity area</b>, you'll find the complete conversation history—every email, every user response, all in one place ✨
<br>
<img src="/assets/helpdesk/desk/ticketActivity.png" style="width: 100%; max-width: 560px;  margin: 16px 0; display: block;">
<br>
When it's time to follow up with a user, just click <b>Reply</b>. Your message will be sent directly to their inbox, keeping the conversation flowing smoothly.
<br>
<img src="/assets/helpdesk/desk/reply.gif" style="width: 100%; max-width: 560px;  margin: 16px 0; display: block;">
<br>
Need to share thoughts or updates with your team instead? Use the <b>Comment</b> feature to leave notes that only your colleagues can see, keeping internal communication clear and organized.
<br>
<img src="/assets/helpdesk/desk/comment.gif" style="width: 100%; max-width: 560px;  margin: 16px 0; display: block;">
<br>
In the <b>Ticket Sidebar</b>, you can manage the ticket. You can assign it to yourself or a teammate, set the priority, type, and customer, and update the status.
<br>
<img src="/assets/helpdesk/desk/sidebar.gif" style="width: 100%; max-width: 560px;  margin: 16px 0; display: block;">
<br>
<b>SLA tracking + source</b> — first response and resolution timers, See where the ticket came from (email or portal)
<br>
<img src="/assets/helpdesk/desk/timers.png" style="width: 100%; max-width: 560px;  margin: 16px 0; display: block;">
<br><br>
What you can do next:<br>
<ul style="padding-left: 20px; margin: 0;">
  <li>Connect your support email to start receiving real tickets</li>
  <li>Invite your team and auto-assign tickets</li>
  <li>Set up SLAs to manage response times</li>
  <li>Add a Knowledge Base for self-serve support</li>
  <li>Enable the customer portal for ticket tracking</li>
</ul>
<br>
You can explore on your own, or just reply to this ticket to see how it works.
<br>
If you need help, reach out to us here: <a href="https://support.frappe.io/helpdesk" style="color: #3b82f6;">https://support.frappe.io/helpdesk</a>
<br><br>
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

    # Render template with the current user's information
    user_doc = frappe.get_doc("User", frappe.session.user)
    rendered_content = frappe.render_template(CONTENT, {"user": user_doc})

    d = frappe.new_doc("HD Ticket")
    d.subject = "Welcome to Helpdesk"
    d.description = rendered_content
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
