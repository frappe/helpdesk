from typing import Literal

import frappe
from frappe.core.api.user_invitation import invite_by_email
from frappe.desk.reportview import delete_bulk
from frappe.utils import validate_phone_number_with_country_code

from helpdesk.utils import get_country_from_timezone, get_customers


@frappe.whitelist(methods=["GET"])
def search_contacts(
    txt: str, additional_filters: str | list | None = None
) -> list[dict[Literal["full_name", "name", "email_id"], str]]:
    doctype = "Contact"
    filters: list[list] = [[doctype, "email_id", "is", "set"]]
    if additional_filters:
        if isinstance(additional_filters, str):
            additional_filters = frappe.parse_json(additional_filters)
        filters.extend(additional_filters)
    or_filters: list[list[str]] = []
    search_fields = ["full_name", "email_id", "name"]
    if txt:
        for field in search_fields:
            or_filters.append([doctype, field, "like", f"%{txt}%"])
    return frappe.get_list(
        doctype,
        filters=filters,
        fields=search_fields,
        or_filters=or_filters,
        limit_start=0,
        limit_page_length=10,
        order_by="email_id, full_name, name",
        ignore_permissions=False,
        strict=False,
    )


@frappe.whitelist()
def delete_contact(name: str, delete_tickets: bool = False):
    # TODO: add as on_trash hook in hooks to handle this at the DocType level
    frappe.has_permission("Contact", "delete", throw=True)

    tickets = frappe.get_list("HD Ticket", filters={"contact": name}, pluck="name")
    frappe.has_permission("HD Ticket", "write", throw=True)
    frappe.db.set_value("HD Ticket", tickets, "contact", None)

    if delete_tickets:
        frappe.has_permission("HD Ticket", "delete", throw=True)
        delete_bulk("HD Ticket", tickets)

    unlink_from_customers(name)

    frappe.db.set_value(
        "User Invitation",
        {"contact": name, "app_name": "helpdesk"},
        "contact",
        None,
    )
    frappe.delete_doc("Contact", name)


def unlink_from_customers(name: str):
    customers = frappe.get_all(
        "HD Customer Member",
        filters={"contact_name": name},
        pluck="parent",
    )

    for customer in customers:
        customer_doc = frappe.get_doc("HD Customer", customer)
        contacts = customer_doc.get("contacts", [])
        contacts = [c for c in contacts if c.contact_name != name]
        customer_doc.contacts = contacts

        if customer_doc.primary_contact == name:
            customer_doc.primary_contact = None
            customer_doc.email_id = None
            customer_doc.mobile_no = None
        customer_doc.save()


@frappe.whitelist()
def create_contact(doc: dict, invite: bool = False) -> str:
    frappe.has_permission("Contact", "create", throw=True)
    phone = doc.get("phone")
    if phone:
        validate_phone_number_with_country_code(phone, "Phone")

    contact_doc = frappe.get_doc(
        {
            "doctype": "Contact",
            "first_name": doc.get("first_name"),
            "last_name": doc.get("last_name"),
            "image": doc.get("image"),
        }
    )

    if email := doc.get("email"):
        contact_doc.append("email_ids", {"email_id": email, "is_primary": True})

    if phone:
        contact_doc.append(
            "phone_nos",
            {"phone": phone, "is_primary_phone": True, "is_primary_mobile_no": True},
        )

    contact_doc.insert()
    if invite:
        invite_by_email(
            email,
            ["HD Customer"],
            redirect_to_path="/helpdesk",
            app_name="helpdesk",
            contact=contact_doc.name,
            customer=doc.get("customer"),
        )
        contact_doc.reload()

    return contact_doc.get("name")


@frappe.whitelist(methods=["POST"])
def edit_contact(name: str, doc: dict):
    frappe.has_permission("Contact", "write", throw=True)
    contact_doc = frappe.get_doc("Contact", name)

    contact_doc.first_name = doc.get("first_name", contact_doc.first_name)
    contact_doc.last_name = doc.get("last_name", contact_doc.last_name)
    contact_doc.image = doc.get("image", contact_doc.image)

    email_ids = doc.get("email_ids")
    if email_ids is not None:
        contact_doc.email_ids = []
        for e in email_ids:
            contact_doc.append(
                "email_ids",
                {"email_id": e.get("email_id"), "is_primary": e.get("is_primary")},
            )

    phone_nos = doc.get("phone_nos")
    if phone_nos is not None:
        for index, p in enumerate(phone_nos, start=1):
            if phone := p.get("phone"):
                validate_phone_number_with_country_code(phone, f"Phone-row {index}")
        contact_doc.phone_nos = []
        for p in phone_nos:
            contact_doc.append(
                "phone_nos",
                {
                    "phone": p.get("phone"),
                    "is_primary_phone": p.get("is_primary"),
                    "is_primary_mobile_no": p.get("is_primary"),
                },
            )

    contact_doc.save()

    if user := contact_doc.get("user"):
        user_doc = frappe.get_doc("User", user)
        user_doc.user_image = doc.get("image", "")
        user_doc.time_zone = doc.get("timezone", "")
        user_doc.save()

    return contact_doc.name


@frappe.whitelist(methods=["GET"])
def get_contact_info(name: str) -> dict:
    frappe.has_permission("Contact", "read", doc=name, throw=True)
    contact = frappe.get_doc("Contact", name)
    primary_email = contact.email_ids[0].email_id if contact.email_ids else None

    result = {
        "customers": get_customers_with_image(name),
        "invitation": get_invitation(name, primary_email),
    }
    if contact.user:
        time_zone = frappe.db.get_value("User", contact.user, "time_zone")
        if time_zone:
            result["timezone"] = time_zone
            result["country"] = get_country_from_timezone(time_zone)
    return result


def get_customers_with_image(name: str) -> list[dict]:
    customers = get_customers(contact=name)
    return [
        {"name": c, "image": frappe.db.get_value("HD Customer", c, "image")}
        for c in customers
    ]


def get_invitation(name: str, email: str | None) -> dict | None:
    if not email:
        return None
    return frappe.db.get_value(
        "User Invitation",
        {
            "contact": name,
            "status": ["!=", "Accepted"],
            "email": email,
            "app_name": "helpdesk",
        },
        ["name", "status"],
        as_dict=True,
        order_by="creation desc",
    )
