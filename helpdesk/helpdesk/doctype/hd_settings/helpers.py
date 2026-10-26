import frappe
from frappe.utils import get_datetime

from helpdesk.utils import CUSTOMER_PORTAL_ROOT


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
   <div style="margin-bottom: 10px">
    <p style="margin-bottom: 20px">Message</p>
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


default_banner_msg = """Thanks for reaching out 👋. This ticket was created outside our working hours. You can expect the next response by {{ next_working_day }}."""


@frappe.whitelist()
def get_banner_msg():
    """Get current and default banner message for settings UI"""

    current_msg = frappe.db.get_single_value(
        "HD Settings", "outside_working_hours_message"
    )
    enabled = frappe.db.get_single_value("HD Settings", "enable_outside_hours_banner")

    return {
        "default": default_banner_msg,
        "current": current_msg or None,
        "enabled": bool(enabled),
    }


def get_rendered_banner_msg(ticket_id):
    banner_msg = frappe.db.get_single_value(
        "HD Settings", "outside_working_hours_message"
    )
    ticket = frappe.get_doc("HD Ticket", ticket_id).as_dict()
    if not banner_msg:
        banner_msg = default_banner_msg

    next_working_day = None
    next_working_date = None
    expected_response = None

    if ticket.get("response_by"):
        next_working_day_dt = get_datetime(ticket.get("response_by"))
        next_working_day = next_working_day_dt.strftime("%A, %d %b")
        next_working_date = next_working_day_dt.strftime("%d %b")
        expected_response = next_working_day_dt.strftime("%H:%M, %A, %d %b")

    context = {
        "ticket": ticket,
        "next_working_daytime": next_working_day_dt,
        "next_working_day": next_working_day,
        "next_working_date": next_working_date,
        "expected_response": expected_response,
    }

    rendered = frappe.render_template(banner_msg, context)

    return {
        "banner_msg": rendered,
    }


KNOWLEDGE_BASE_HOME = CUSTOMER_PORTAL_ROOT
TICKETS_HOME = f"{CUSTOMER_PORTAL_ROOT}/my-tickets"


def sync_home_page_to_website_settings(settings) -> None:
    """Guests at the site root see the knowledge base while the setting is on.
    Turning it off clears the home page only if it is still ours."""
    if not settings.has_value_changed("knowledge_base_home_page_for_guests"):
        return
    if settings.knowledge_base_home_page_for_guests:
        set_website_home_page(KNOWLEDGE_BASE_HOME.strip("/"))
    else:
        clear_website_home_page()


def set_website_home_page(home_page: str) -> None:
    frappe.db.set_single_value("Website Settings", "home_page", home_page)
    # set_single_value skips Website Settings' on_update; home pages are cached per user
    frappe.clear_cache()


def clear_website_home_page() -> None:
    home_page = frappe.db.get_single_value("Website Settings", "home_page")
    if (home_page or "").strip("/") == KNOWLEDGE_BASE_HOME.strip("/"):
        set_website_home_page("")


def get_customer_home_page() -> str:
    if frappe.db.get_single_value("HD Settings", "prefer_knowledge_base"):
        return KNOWLEDGE_BASE_HOME
    return TICKETS_HOME


def sync_brand_to_website_settings(settings) -> None:
    """Site-wide: framework emails, login page and desk read the brand from Website Settings."""
    logo_changed = any(
        settings.has_value_changed(field) for field in ("brand_logo", "favicon")
    )
    name_changed = settings.has_value_changed("brand_name") and settings.brand_name
    if logo_changed:
        # a logo set by hand or by another app stays
        previous = get_brand_image(settings.get_doc_before_save() or frappe._dict())
        current = frappe.db.get_single_value("Website Settings", "app_logo") or ""
        logo_changed = current in ("", previous)
    if logo_changed:
        frappe.db.set_single_value(
            "Website Settings", "app_logo", get_brand_image(settings)
        )
    if name_changed:
        set_site_brand_name(settings.brand_name)
    if logo_changed or name_changed:
        # set_single_value skips Website Settings' on_update, which clears the boot cache
        frappe.clear_cache()


def get_brand_image(settings) -> str:
    """The logo, else the favicon, so an icon-only brand still marks auth emails."""
    return settings.brand_logo or settings.favicon or ""


def set_site_brand_name(brand_name: str) -> None:
    frappe.db.set_single_value("Website Settings", "app_name", brand_name)
    # Display name in framework emails, e.g. the welcome mail "Welcome to <name>".
    frappe.db.set_default("site_name", brand_name)
