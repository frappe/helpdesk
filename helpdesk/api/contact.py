from typing import Literal

import frappe
from frappe.core.api.user_invitation import invite_by_email
from frappe.desk.reportview import delete_bulk


@frappe.whitelist(methods=["GET"])
def search_contacts(
    txt: str,
) -> list[dict[Literal["full_name", "name", "email_id"], str]]:
    doctype = "Contact"
    or_filters: list[list[str]] = []
    search_fields = ["full_name", "email_id", "name"]
    if txt:
        for field in search_fields:
            or_filters.append([doctype, field, "like", f"%{txt}%"])
    return frappe.get_list(
        doctype,
        filters=[[doctype, "email_id", "is", "set"]],
        fields=search_fields,
        or_filters=or_filters,
        limit_start=0,
        limit_page_length=10,
        order_by="email_id, full_name, name",
        ignore_permissions=False,
        strict=False,
    )


@frappe.whitelist()
def delete_contact(name: str):
    # TODO: add as on_trash hook in hooks to handle this at the DocType level
    frappe.has_permission("Contact", "delete", throw=True)
    tickets = frappe.get_list("HD Ticket", filters={"contact": name}, pluck="name")
    delete_bulk("HD Ticket", tickets)
    customers = frappe.get_all(
        "HD Customer Member",
        filters={"contact_name": name},
        pluck="parent",
    )
    delete_bulk("HD Customer Member", customers)
    # user_invitation link remove contact
    frappe.delete_doc("Contact", name)


@frappe.whitelist()
def create_contact(doc: dict, invite: bool = False) -> str:
    frappe.has_permission("Contact", "create", throw=True)
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

    if phone := doc.get("phone"):
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
