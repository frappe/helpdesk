import frappe
from frappe.utils import get_datetime

from helpdesk.helpdesk.doctype.hd_settings.helpers import get_default_banner_msg


@frappe.whitelist()
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
