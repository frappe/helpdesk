import frappe
from frappe.utils import add_to_date, getdate

from helpdesk.api.settings.field_dependency import create_update_field_dependency

SLA_PRIORITY_NAME = "SLA Priority"


def before_tests():
    frappe.db.set_single_value("HD Settings", "skip_email_workflow", 0)  # nosemgrep
    frappe.db.set_single_value(
        "HD Settings", "enable_email_ticket_feedback", 0
    )  # nosemgrep
    # frappe.flags.mute_emails = True
    make_new_sla()
    frappe.db.commit()  # nosemgrep


def make_new_sla():
    condition = "doc.priority in ['High', 'Urgent', 'Low']"
    sla_doc = make_sla(SLA_PRIORITY_NAME, condition)
    sla_doc = sla_doc.reload()

    sla_doc.support_and_resolution = []
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        service_day = frappe.get_doc(
            {
                "doctype": "HD Service Day",
                "workday": day,
                "start_time": "10:00:00",
                "end_time": "18:00:00",
            }
        )
        sla_doc.append("support_and_resolution", service_day)

    low_priority = frappe.get_doc(
        {
            "doctype": "HD Service Level Priority",
            "default_priority": 0,
            "priority": "Low",
            "response_time": 60 * 60 * 24,
            "resolution_time": 60 * 60 * 72,
        }
    )

    medium_priority = frappe.get_doc(
        {
            "doctype": "HD Service Level Priority",
            "default_priority": 1,
            "priority": "Medium",
            "response_time": 60 * 60 * 8,
            "resolution_time": 60 * 60 * 24,
        }
    )

    high_priority = frappe.get_doc(
        {
            "doctype": "HD Service Level Priority",
            "default_priority": 0,
            "priority": "High",
            "response_time": 60 * 60 * 1,
            "resolution_time": 60 * 60 * 4,
        }
    )

    urgent_priority = frappe.get_doc(
        {
            "doctype": "HD Service Level Priority",
            "default_priority": 0,
            "priority": "Urgent",
            "response_time": 60 * 30,
            "resolution_time": 60 * 60 * 2,
        }
    )
    sla_doc.priorities = []
    sla_doc.append("priorities", low_priority)
    sla_doc.append("priorities", medium_priority)
    sla_doc.append("priorities", high_priority)
    sla_doc.append("priorities", urgent_priority)

    sla_doc.save()


def make_sla(sla_name: str = "Test SLA", condition: str = ""):
    def_sla = frappe.get_doc("HD Service Level Agreement", "Default")
    sla_doc = frappe.copy_doc(def_sla)
    sla_doc.service_level = sla_name
    sla_doc.condition = condition
    sla_doc.default_sla = 0
    sla_doc.insert(ignore_if_duplicate=True, ignore_permissions=True)
    return sla_doc


def make_ticket(
    subject: str = "Test Ticket",
    description: str = "This is a test ticket.",
    save: bool = True,
    **args
):
    """
    Creates a test HD Ticket with the given subject, description, priority, and ticket type.
    """
    ticket = frappe.get_doc(
        {"doctype": "HD Ticket", "subject": subject, "description": description, **args}
    )
    if save:
        ticket.insert(ignore_if_duplicate=True, ignore_permissions=True)
    return ticket


def get_current_week_monday(hours: int = 11):
    """
    Returns the current week's Monday date
    """

    current_date = getdate()
    # Get the current week's Monday
    monday = add_to_date(current_date, days=-current_date.weekday(), hours=hours)
    return monday


def get_priority_response_resolution_time(
    sla: str, priority: str, date=None, add_to_time: bool = True
):
    """
    Returns the expected response or resolution time for a given priority.
    """
    sla = frappe.get_doc("HD Service Level Agreement", sla)
    priorities = sla.get_priorities()
    high_priority = priorities[priority]
    first_response = high_priority.response_time
    resolution_time = high_priority.resolution_time
    if not add_to_time:
        return first_response, resolution_time

    date = date or get_current_week_monday()
    expected_response_by = add_to_date(date, seconds=first_response)

    expected_resolution_by = add_to_date(date, seconds=resolution_time)
    return expected_response_by, expected_resolution_by


def add_holiday(date, description="_Test Holiday"):
    """
    Adds a holiday to the system.
    """

    holiday_list = frappe.get_doc("HD Service Holiday List", "Default")
    holiday_list.append(
        "holidays",
        {
            "holiday_date": date,
            "description": description,
        },
    )
    holiday_list.save()


def remove_holidays():
    """
    Removes a holiday from the system.
    """
    holiday_list = frappe.get_doc("HD Service Holiday List", "Default")
    holiday_list.holidays = []
    holiday_list.save()


def create_field_dependency():
    parent_field = "ticket_type"
    child_field = "priority"
    mapping = '{"Unspecified":["Urgent","High"],"Question":["Medium","High"],"Bug":["Medium"],"Incident":["Urgent","High","Medium","Low"]}'
    enabled = 1
    fields_criteria = '{"display":{"enabled":true,"value":[{"label":"Any","value":"Any"}]},"mandatory":{"enabled":true,"value":[{"label":"Question","value":"Question"},{"label":"Bug","value":"Bug"}]}}'

    create_update_field_dependency(
        parent_field, child_field, mapping, enabled, fields_criteria
    )


def make_status(name: str = "Test Status", category: str = "Open"):
    if frappe.db.exists("HD Ticket Status", name):
        return frappe.get_doc("HD Ticket Status", name)

    doc = frappe.get_doc(
        {
            "doctype": "HD Ticket Status",
            "label_agent": name,
            "category": category,
            "is_default": 0,
        }
    )
    return doc.insert(ignore_if_duplicate=True)
