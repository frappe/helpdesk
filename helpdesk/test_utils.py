from datetime import datetime

import frappe
from frappe.core.doctype.communication.test_communication import create_email_account
from frappe.utils import add_to_date, getdate

from helpdesk.api.settings.field_dependency import create_update_field_dependency
from helpdesk.utils import get_customers, is_frappe_version

if is_frappe_version("16", above=True):
    from frappe.tests.utils import make_test_objects
else:
    from frappe.test_runner import make_test_objects


SLA_PRIORITY_NAME = "SLA Priority"
TEST_HOLIDAY_LIST_NAME = "Test Holiday List"


def before_tests():
    frappe.db.set_single_value("HD Settings", "skip_email_workflow", 0)  # nosemgrep
    frappe.db.set_single_value(
        "HD Settings", "enable_email_ticket_feedback", 0
    )  # nosemgrep
    # frappe.flags.mute_emails = True
    make_holiday_list()
    make_new_sla()
    make_test_objects("Email Domain", reset=True)
    create_email_account()
    frappe.db.commit()  # nosemgrep


def make_new_sla():
    condition = "doc.priority in ['High', 'Urgent', 'Low']"
    sla_doc = make_sla(SLA_PRIORITY_NAME, condition)
    sla_doc = sla_doc.reload()
    sla_doc.holiday_list = TEST_HOLIDAY_LIST_NAME

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


def make_holiday_list():
    if not frappe.db.exists("HD Service Holiday List", TEST_HOLIDAY_LIST_NAME):
        # from_date = first date of current year
        from_date = datetime(datetime.today().year, 1, 1).date()
        to_date = datetime(datetime.today().year + 1, 1, 15).date()
        frappe.get_doc(
            {
                "doctype": "HD Service Holiday List",
                "holiday_list_name": TEST_HOLIDAY_LIST_NAME,
                "from_date": from_date,
                "to_date": to_date,
            }
        ).insert()


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
    **args,
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


def create_agent(
    email: str, first_name: str | None = None, last_name: str | None = None
):
    """
    Creates a test agent user with the Agent role.
    """
    if not frappe.db.exists("User", email):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name or email.split("@")[0],
                "last_name": last_name or "Agent",
                "send_welcome_email": 0,
            }
        )
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", email)

    if "Agent" not in frappe.get_roles(email):
        user.add_roles("Agent")

    agent_name = f"{user.first_name} {user.last_name or ''}".strip()
    existing_agent = frappe.db.exists("HD Agent", {"user": email})
    if not existing_agent:
        frappe.get_doc(
            {
                "doctype": "HD Agent",
                "user": email,
                "agent_name": agent_name or email,
                "is_active": 1,
            }
        ).insert(ignore_permissions=True)

    return user


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


def add_holiday(holiday_date, description="_Test Holiday"):
    """
    Adds a holiday to the system.
    """

    holiday_list_doc = frappe.get_doc("HD Service Holiday List", "Test Holiday List")
    holiday_list_doc.append(
        "holidays",
        {
            "holiday_date": holiday_date,
            "description": description,
        },
    )
    holiday_list_doc.save()


def remove_holidays():
    """
    Removes a holiday from the system.
    """
    holiday_list = frappe.get_doc("HD Service Holiday List", TEST_HOLIDAY_LIST_NAME)
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


def make_agent(email: str, first_name: str = "Test Agent"):
    """
    Creates a test user and HD Agent if they don't exist.
    Returns the user email.
    """
    if not frappe.db.exists("User", email):
        frappe.get_doc(
            {"doctype": "User", "first_name": first_name, "email": email}
        ).insert(ignore_permissions=True)

    if not frappe.db.exists("HD Agent", {"user": email}):
        frappe.get_doc(
            {"doctype": "HD Agent", "user": email, "agent_name": first_name}
        ).insert(ignore_permissions=True)

    return email


def add_comment(
    ticket: str,
    content: str = "This is a test comment.",
    comment_by: str | None = None,
    save: bool = True,
):
    """
    Creates a test HD Ticket Comment for a given ticket.
    """
    comment = frappe.get_doc(
        {
            "doctype": "HD Ticket Comment",
            "reference_ticket": ticket,
            "content": content,
            "comment_by": comment_by,
        }
    )
    if save:
        return comment.insert()
    return comment


def create_contact(name, email, user=True, role="HD Customer"):
    result = {}

    # Delete any existing contacts with this email so we always start clean
    existing = frappe.db.get_all("Contact", filters={"email_id": email}, pluck="name")
    for c in existing:
        frappe.delete_doc("Contact", c, force=True)

    contact = frappe.get_doc(
        {
            "doctype": "Contact",
            "first_name": name,
            # top-level email_id is what set_contact() queries via
            # frappe.db.get_value("Contact", {"email_id": email_id})
            "email_id": email,
        }
    )
    contact.append("email_ids", {"email_id": email, "is_primary": 1})
    contact.insert()

    result["contact"] = contact.name
    if not user:
        return result

    if frappe.db.exists("User", email):
        # User may have linked docs (tickets) — just strip roles and reuse
        _user = frappe.get_doc("User", email)
        _user.roles = []
        _user.save(ignore_permissions=True)
    else:
        _user = frappe.get_doc({"doctype": "User", "first_name": name, "email": email})
        _user.insert(ignore_permissions=True)

    _user.add_roles(role)

    # link the user to the contact so get_customers(user=email) resolves correctly
    frappe.db.set_value("Contact", contact.name, "user", _user.name)

    result["user"] = _user.name
    return result


def create_customer(name, contacts=[]):
    if frappe.db.exists("HD Customer", name):
        frappe.delete_doc("HD Customer", name, force=True)

    customer = frappe.get_doc({"doctype": "HD Customer", "customer_name": name})

    for c in contacts:
        customer.append("contacts", c)
    return customer.insert()


def update_role_in_customer(customer, contact, role="HD Customer", is_primary=False):
    frappe.set_user("Administrator")
    is_manager = True if role == "HD Customer Manager" else False

    for c in customer.get("contacts", []):
        if c.get("contact_name") != contact:
            continue
        c.is_manager = is_manager
        c.is_primary = is_primary

    customer.save()


def add_contact_in_customer(customer, contact, is_manager=False, is_primary=False):
    frappe.set_user("Administrator")
    customer.append(
        "contacts",
        {"contact_name": contact, "is_manager": is_manager, "is_primary": is_primary},
    )
    for c in customer.get("contacts", []):
        if c.get("contact_name") != contact and is_primary:
            c.is_primary = False

    customer.save()


def cleanup_contact_users(contacts, customers=[]):
    frappe.set_user("Administrator")
    for contact in contacts:
        contact_name = contact.get("contact")
        user_email = contact.get("user")

        # remove from any customer
        linked_customers = get_customers(contact=contact_name)
        for customer in linked_customers:
            customer_doc = frappe.get_doc("HD Customer", customer)
            customer_doc.contacts = [
                c
                for c in customer_doc.contacts
                if c.get("contact_name") != contact_name
            ]
            customer_doc.save()

        if user_email and frappe.db.exists("User", user_email):
            frappe.delete_doc("User", user_email, force=True)

        existing = (
            frappe.db.get_all("Contact", filters={"email_id": user_email}, pluck="name")
            if user_email
            else []
        )
        for c in existing:
            frappe.delete_doc("Contact", c, force=True)

    for c in customers:
        if frappe.db.exists("HD Customer", c):
            frappe.delete_doc("HD Customer", c, force=True)
        if frappe.db.exists("HD Customer", c):
            frappe.delete_doc("HD Customer", c, force=True)
            frappe.delete_doc("HD Customer", c, force=True)
            frappe.delete_doc("HD Customer", c, force=True)
            frappe.delete_doc("HD Customer", c, force=True)
            frappe.delete_doc("HD Customer", c, force=True)
