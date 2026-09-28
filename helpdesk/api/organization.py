"""Backs the portal's settings modal: the caller's organizations and who is in them."""

import frappe
from frappe import _
from frappe.utils import sbool

from helpdesk.api.dashboard import COUNT_NAME
from helpdesk.helpdesk.doctype.hd_customer.hd_customer import CUSTOMER_ROLES
from helpdesk.utils import CUSTOMER_PORTAL_ROOT, get_customers

MANAGER_ROLE = "HD Customer Manager"
PORTAL_INVITE_SETTING = "allow_customer_managers_to_invite"
PORTAL_EDIT_SETTING = "allow_customer_managers_to_edit_organization"
# Organizations the caller can act on come first; alphabetical within a role.
ROLE_ORDER = {"Owner": 0, "Manager": 1, "Member": 2}


@frappe.whitelist()
def get_settings() -> dict:
    """The session user's profile plus every organization they belong to."""
    user = frappe.db.get_value(
        "User",
        frappe.session.user,
        [
            "name",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "user_image as image",
        ],
        as_dict=True,
    )
    return {"user": user, "organizations": _get_organizations()}


@frappe.whitelist()
def get_organization(customer: str) -> dict:
    """One organization the caller belongs to, with everyone in it."""
    hd_customer = frappe.get_doc("HD Customer", customer)
    hd_customer.check_permission("read")
    is_manager = hd_customer.has_permission("write")
    return {
        "name": hd_customer.name,
        "customer_name": hd_customer.customer_name,
        "image": hd_customer.image,
        "domain": hd_customer.domain,
        "email": hd_customer.email_id or hd_customer.owner,
        "country": hd_customer.country,
        "is_manager": is_manager,
        "can_invite": is_manager and _is_portal_setting_on(PORTAL_INVITE_SETTING),
        "can_edit": is_manager and _is_portal_setting_on(PORTAL_EDIT_SETTING),
        "members": _get_members(hd_customer) + _get_pending_members(hd_customer),
    }


@frappe.whitelist()
def get_invitable_contacts(customer: str) -> list[dict]:
    """Contacts on the organization's email domain with a login, minus agents, members
    and pending invitees."""
    hd_customer = _get_managed_customer(customer, PORTAL_INVITE_SETTING)
    if not hd_customer.domain:
        return []
    excluded_emails = [row["email"] for row in hd_customer.get_pending_invitations()]
    excluded_emails += frappe.get_all("HD Agent", pluck="name")
    return frappe.get_all(
        "Contact",
        filters=[
            ["user", "is", "set"],
            ["email_id", "like", f"%@{hd_customer.domain}"],
            ["email_id", "not in", excluded_emails],
            ["name", "not in", [row.contact_name for row in hd_customer.contacts]],
        ],
        fields=["full_name", "email_id as email", "image"],
        order_by="full_name asc",
    )


@frappe.whitelist()
def invite_members(customer: str, emails: list[str], role: str) -> None:
    """Inserted with permissions ignored because customer managers hold none on User
    Invitation; `HelpdeskUserInvitation` still checks they manage this customer."""
    hd_customer = _get_managed_customer(customer, PORTAL_INVITE_SETTING)
    if role not in CUSTOMER_ROLES:
        frappe.throw(_("Invalid role {0}").format(role))
    for email in emails:
        frappe.get_doc(
            doctype="User Invitation",
            email=email,
            roles=[{"role": role}],
            app_name="helpdesk",
            redirect_to_path=CUSTOMER_PORTAL_ROOT,
            customer=hd_customer.name,
            contact=frappe.db.get_value("Contact", {"email_id": email}),
        ).insert(ignore_permissions=True)


@frappe.whitelist()
def update_member_role(customer: str, contact: str, is_manager: bool) -> None:
    hd_customer = _get_managed_customer(customer, PORTAL_INVITE_SETTING)
    member = _get_editable_member(hd_customer, contact)
    member.is_manager = int(sbool(is_manager))
    hd_customer.save()


@frappe.whitelist()
def remove_member(
    customer: str, contact: str | None = None, invitation: str | None = None
) -> None:
    """Drop a member, or cancel the invitation of someone who has not joined yet."""
    hd_customer = _get_managed_customer(customer, PORTAL_INVITE_SETTING)
    if invitation:
        return _cancel_invitation(hd_customer, invitation)
    _get_editable_member(hd_customer, contact)
    hd_customer.remove_contact(contact)
    hd_customer.save()


@frappe.whitelist()
def update_organization(
    customer: str, customer_name: str | None = None, image: str | None = None
) -> str:
    """Rename or re-logo an organization you manage; answers with its current docname."""
    hd_customer = _get_managed_customer(customer, PORTAL_EDIT_SETTING)
    if image is not None:
        hd_customer.image = image or None
        hd_customer.save()
    if customer_name and customer_name != hd_customer.name:
        return frappe.rename_doc("HD Customer", hd_customer.name, customer_name)
    return hd_customer.name


def _get_organizations() -> list[dict]:
    memberships = {
        row["name"]: row["is_manager"] for row in get_customers(get_roles=True)
    }
    if not memberships:
        return []
    session_contact = _get_session_contact()
    member_counts = _count_rows_by("HD Customer Member", "parent", list(memberships))
    ticket_counts = _count_rows_by("HD Ticket", "customer", list(memberships))
    rows = frappe.get_all(
        "HD Customer",
        filters={"name": ["in", list(memberships)]},
        fields=["name", "customer_name", "image", "domain", "primary_contact"],
    )
    organizations = [
        {
            "name": row.name,
            "customer_name": row.customer_name,
            "image": row.image,
            "domain": row.domain,
            "role": _get_role_label(
                row.primary_contact == session_contact, memberships[row.name]
            ),
            "member_count": member_counts.get(row.name, 0),
            "ticket_count": ticket_counts.get(row.name, 0),
        }
        for row in rows
    ]
    organizations.sort(
        key=lambda org: (ROLE_ORDER[org["role"]], (org["customer_name"] or "").lower())
    )
    return organizations


def _get_members(hd_customer) -> list[dict]:
    contact_names = [row.contact_name for row in hd_customer.contacts]
    details = hd_customer.get_contact_details(contact_names)
    last_active = hd_customer.get_last_active(
        [contact.user for contact in details.values() if contact.user]
    )
    session_contact = _get_session_contact()
    members = []
    for row in hd_customer.contacts:
        contact = details.get(row.contact_name)
        if not contact:
            continue
        is_owner = row.contact_name == hd_customer.primary_contact
        members.append(
            {
                "contact": row.contact_name,
                "full_name": contact.full_name,
                "email": contact.email_id,
                "image": contact.image,
                "role": _get_role_label(is_owner, row.is_manager),
                "is_you": row.contact_name == session_contact,
                "last_seen": last_active.get(contact.user),
            }
        )
    members.sort(
        key=lambda member: (ROLE_ORDER[member["role"]], member["full_name"].lower())
    )
    return members


def _get_pending_members(hd_customer) -> list[dict]:
    return [
        {
            "invitation": invitation["name"],
            "full_name": invitation["email"].split("@")[0],
            "email": invitation["email"],
            "role": _get_role_label(False, MANAGER_ROLE in invitation["roles"]),
            "pending": True,
        }
        for invitation in hd_customer.get_pending_invitations()
    ]


def _get_role_label(is_owner: bool, is_manager: bool) -> str:
    if is_owner:
        return "Owner"
    return "Manager" if is_manager else "Member"


def _count_rows_by(doctype: str, fieldname: str, values: list[str]) -> dict[str, int]:
    rows = frappe.get_all(
        doctype,
        filters={fieldname: ["in", values]},
        fields=[fieldname, COUNT_NAME],
        group_by=fieldname,
    )
    return {row[fieldname]: row["count"] for row in rows}


def _get_session_contact() -> str | None:
    return frappe.db.get_value("Contact", {"user": frappe.session.user})


def _is_portal_setting_on(setting: str) -> bool:
    return bool(frappe.db.get_single_value("HD Settings", setting))


def _get_managed_customer(customer: str, setting: str):
    """The HD Customer, once the helpdesk allows the action and the caller manages it."""
    if not _is_portal_setting_on(setting):
        frappe.throw(_("Your helpdesk does not allow this"), frappe.PermissionError)
    hd_customer = frappe.get_doc("HD Customer", customer)
    hd_customer.check_permission("write")
    return hd_customer


def _get_editable_member(hd_customer, contact: str):
    """The membership row, which is neither the owner's nor the caller's own."""
    if contact == hd_customer.primary_contact:
        frappe.throw(_("The owner's membership cannot be changed"))
    if contact == _get_session_contact():
        frappe.throw(_("You cannot change your own membership"))
    member = next(
        (row for row in hd_customer.contacts if row.contact_name == contact), None
    )
    if not member:
        frappe.throw(_("{0} is not a member of {1}").format(contact, hd_customer.name))
    return member


def _cancel_invitation(hd_customer, invitation: str) -> None:
    user_invitation = frappe.get_doc("User Invitation", invitation)
    if user_invitation.customer != hd_customer.name:
        frappe.throw(
            _("This invitation does not belong to your organization"),
            frappe.PermissionError,
        )
    user_invitation.flags.ignore_permissions = True
    user_invitation.cancel_invite()
