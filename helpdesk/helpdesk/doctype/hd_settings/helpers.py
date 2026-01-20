import frappe
from frappe.utils import get_datetime


def is_email_content_empty(content: str | None) -> bool:
    return content is None or content.strip() == ""


def get_default_email_content(type: str) -> str:
    if type == "share_feedback":
        return """\
<p>Hello,</p>
<p>Thanks for reaching out to us. We’d love your feedback on your recent support experience with ticket #{{ doc.name }}.</p>
<a href="{{ url }}" class="btn btn-primary">Share Feedback</a>

<p>Thank you!<br>Support Team</p>"""

    if type == "acknowledgement":
        return """\
<p>Hi,</p>
<br />
<p>Thank you for reaching out to us. We've received your request and created a support ticket.</p>
<p>
    <strong>Ticket ID:</strong> {{ doc.name }}<br />
    <strong>Subject:</strong> {{ doc.subject }}<br />
</p>
<p>Our team is reviewing it and will get back to you shortly.</p>
<br />
<p>Best,<br />Support Team</p>
"""

    if type == "reply_to_agents":
        return """\
<div>
  <p>Hello,</p>
  <p>You have a new reply on the ticket <strong>#{{ doc.name }}</strong>.</p>
  <p><strong>Subject:</strong> {{ doc.subject }}</p>
  <p><strong>Raised By:</strong> {{ doc.raised_by }}</p>
  <p><strong>Priority:</strong> {{ doc.priority }}</p>

  <br />
  <p>
    You can view and respond to this ticket by
    <a href="{{ ticket_url }}">clicking here</a>.
  </p>
  <p>Regards,<br />Support Team</p>
</div>
"""

    if type == "reply_via_agent":
        return """\
<div>
  <h2><strong>Ticket #{{ doc.name }}</strong></h2>
  <h3>You have a new reply on this ticket</h3>
  <br />
  <div style="margin-bottom: 10px">
    <h3 style="margin-bottom: 20px">Message</h3>
    <div
      style="
        background: #f3f5f8;
        padding: 10px;
        border-radius: 4px;
        border: 1px solid #e5e9ee;
      "
    >
      {{ message }}
    </div>
  </div>
  <p>Please visit the customer portal to reply to this message</p>
  <a
    class="btn btn-primary"
    href="{{ ticket_url }}"
    rel="noopener noreferrer"
    target="_blank"
  >View in Portal</a>
  <br />
</div>
"""


def get_default_banner_msg():
    return """Thanks for reaching out 👋. This ticket was created outside our working hours.
You can expect the next response by {{ next_working_day }}."""


@frappe.whitelist()
def check_banner_msg():
    """Get current and default banner message for settings UI"""
    current_msg = frappe.db.get_single_value("HD Settings", "working_hours_message")
    default_msg = get_default_banner_msg()
    enabled = frappe.db.get_single_value("HD Settings", "working_hours_notification")

    return {
        "default": default_msg,
        "current": current_msg or default_msg,
        "enabled": bool(enabled),
    }


def get_rendered_banner_msg(ticket_id):
    banner_msg = frappe.db.get_single_value("HD Settings", "working_hours_message")
    ticket = frappe.get_doc("HD Ticket", ticket_id).as_dict()
    if not banner_msg:
        get_default_banner_msg()

    next_working_day = None
    next_working_daytime = None
    next_working_date = None
    expected_response = None

    if ticket.get("response_by"):
        next_working_day_dt = get_datetime(ticket.get("response_by"))
        next_working_day = next_working_day_dt.strftime("%A, %d %b")
        next_working_date = next_working_day_dt.strftime("%d %b")
        expected_response = next_working_day_dt.strftime("%H:%M, %A, %d %b")

    context = {
        "ticket": ticket,
        "next_working_day": next_working_day,
        "next_working_daytime": next_working_daytime,
        "next_working_date": next_working_date,
        "expected_response": expected_response,
    }

    rendered = frappe.render_template(banner_msg, context)

    return {
        "banner_msg": rendered,
    }


@frappe.whitelist()
def update_banner_settings(enabled: bool, content: str):
    settings = frappe.get_single("HD Settings")
    settings.working_hours_notification = enabled
    settings.working_hours_message = content
    settings.save(ignore_permissions=True)

    return {
        "enabled": settings.working_hours_notification,
        "content": settings.working_hours_message or get_default_banner_msg(),
    }
