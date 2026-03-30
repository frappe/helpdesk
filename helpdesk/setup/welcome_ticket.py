import frappe
from frappe.desk.form.assign_to import add as add_assign

AUTHOR_EMAIl = "john@example.com"
AUTHOR_NAME = "John Doe"
CONTENT = """
<div style="font-family: 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.8; color: #374151; max-width: 560px; margin: 0 auto;">
Hey {{ first_name }} 👋,
<br><br>
We thought we'd use this space to give you a quick walkthrough while you're here. 🙂
<br><br>
This is a sample ticket we created to show you how Frappe Helpdesk works.
<br><br>
Getting started is easy. In the main <b>Ticket activity area</b>, when you reply to a ticket your response shows up directly below in the activity thread. This way you can keep track of all your ticket activities in one single place. ✨
<br>
<img src="/assets/helpdesk/desk/ticketActivity.png" style="width: 100%; max-width: 560px;  margin: 16px 0; border-radius: 10px; display: block;">
<br>
When it's time to follow up with a user, just click <b>Reply</b>. Your message will be sent directly to their inbox, keeping the conversation flowing smoothly.
<br>
<video autoplay loop muted  src="/assets/helpdesk/desk/videos/mailVideo.mp4" style="width: 100%; max-width: 560px;  margin: 16px 0; border-radius: 10px; display: block;"></video>
<br>
Want to discuss a ticket with your team internally? Utilize the <b>Comment</b> feature to leave notes that are visible only to your colleagues, ensuring that internal communication remains clear, organized, and private.<br>
<video autoplay loop muted src="/assets/helpdesk/desk/videos/commentVideo.mp4" style="width: 100%; max-width: 560px;  margin: 16px 0; border-radius: 10px; display: block;"></video>
<br>
In the <b>Ticket Sidebar</b>, you can manage the ticket. You can assign it to yourself or a teammate, set the priority, ticket type and also update the ticket status.
<br>
<video autoplay loop muted  src="/assets/helpdesk/desk/videos/sidebarVideo.mp4" style="width: 100%; max-width: 560px;  margin: 16px 0; border-radius: 10px; display: block;"></video>
<br>
Inside the <b>Ticket Header</b>, you can view the first response and resolution timers. Additionally, you can also see the source of the ticket, whether it came from email or the support portal.
<br>
<img src="/assets/helpdesk/desk/timers.png" style="width: 100%; max-width: 560px;  margin: 16px 0; border-radius: 10px; display: block;">
<br><br>
That's pretty much how it works.
<br><br>
What you can do next:<br>
<ul style="padding-left: 20px; margin: 0;">
  <li>Connect your support email to start receiving real tickets.</li>
  <li>Invite your team and auto-assign tickets using assignment rules.</li>
  <li>Set up SLAs to manage response times for your agents.</li>
  <li>Add a Knowledge Base for self-serve support.</li>
  <li>Check out our documentation at <a href="https://docs.frappe.io/helpdesk" style="color: #3b82f6;">https://docs.frappe.io/helpdesk</a> </li>
</ul>
<br>
Feel free to click around and explore our product.
<br><br>
If you need help, reach out to us here: <a href="https://support.frappe.io/helpdesk" style="color: #3b82f6;">https://support.frappe.io/helpdesk</a>
<br><br>
Cheers,<br>
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
    if (user_doc.name or "").strip().lower() == "administrator":
        first_name = "there"
    else:
        first_name = (user_doc.first_name or "").strip() or "there"
    rendered_content = frappe.render_template(
        CONTENT,
        {
            "first_name": first_name,
        },
        safe_render=True,
    )

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
