from typing import Literal

import frappe
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
    frappe.delete_doc("Contact", name)


@frappe.whitelist()
def create_contact(doc: dict) -> str:
    print(doc.get("image"))

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

    # Link contact to customer if customer is provided, creates user of contact and assign HD Customer role to the user
    if customer := doc.get("customer"):
        customer_doc = frappe.get_doc("HD Customer", customer)
        customer_doc.append("contacts", {"contact_name": contact_doc.name})
        customer_doc.save()

        contact_doc.reload()  # reload to get the linked user

        # If contact is linked to a customer, then they should have a user.
        user = contact_doc.get("user")
        user_doc = frappe.get_doc("User", user)
        user_doc.image = doc.get("image", "")
        user_doc.timezone = doc.get("timezone", "")
        user_doc.save()

    return contact_doc.get("name")
