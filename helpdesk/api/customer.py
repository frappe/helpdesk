import frappe
from frappe import _
from frappe.model.document import Document
from frappe.rate_limiter import rate_limit
from frappe.utils import add_to_date, get_fullname, now_datetime, sbool

from helpdesk.api.auth import validate_uploaded_image
from helpdesk.api.contact import create_contact
from helpdesk.api.dashboard import COUNT_NAME
from helpdesk.helpdesk.doctype.hd_customer.hd_customer import (
    MANAGER_ROLE,
    is_customer_manager,
)
from helpdesk.utils import (
    CUSTOMER_PORTAL_ROOT,
    get_customers,
    get_user_contact,
    is_agent_manager,
)

ROLE_ORDER = {"Owner": 0, "Manager": 1, "Member": 2}
MAX_INVITES = 20
# invitation emails one manager may send an hour, whatever the batch size
MAX_INVITES_PER_HOUR = 50
MAX_SUGGESTIONS = 50
# Shared by strangers: never suggest invitees from these.
PUBLIC_EMAIL_DOMAINS = frozenset(
    {
        "aol.com",
        "gmail.com",
        "googlemail.com",
        "gmx.com",
        "hotmail.com",
        "icloud.com",
        "live.com",
        "mail.com",
        "me.com",
        "msn.com",
        "outlook.com",
        "proton.me",
        "protonmail.com",
        "rediffmail.com",
        "yahoo.co.in",
        "yahoo.com",
        "yandex.com",
        "zoho.com",
    }
)


@frappe.whitelist()
def create_customer(customer: dict, primary_contact: dict | None = None) -> dict:
    """Create an HD Customer and optionally invite a primary contact.

    The primary contact is created, invited by email and set as the customer's
    primary contact in a single operation. Returns the customer name and the
    emails an invitation was sent to.
    """
    frappe.has_permission("HD Customer", "create", throw=True)

    customer_doc = frappe.get_doc(
        {
            "doctype": "HD Customer",
            "customer_name": customer.get("customer_name"),
            "customer_type": customer.get("customer_type"),
            "domain": customer.get("domain"),
            "image": customer.get("image"),
            "country": customer.get("country"),
        }
    )
    customer_doc.insert()

    invited_emails: list[str] = []
    if primary_contact and primary_contact.get("email"):
        invited_emails = add_primary_contact(customer_doc, primary_contact)

    return {"name": customer_doc.name, "invited_emails": invited_emails}


def add_primary_contact(customer_doc: Document, primary_contact: dict) -> list[str]:
    """Set the primary contact, reusing an existing contact for the email.

    The contact is created first when the email is unknown, so the form's
    name and phone are kept; add_contacts then adds it directly if it has a
    linked user and invites it by email otherwise.
    """
    email = primary_contact.get("email")
    contact_name = frappe.db.get_value("Contact", {"email_id": email}, "name")
    if not contact_name:
        contact_name = create_contact(
            {
                "first_name": primary_contact.get("first_name"),
                "last_name": primary_contact.get("last_name"),
                "email": email,
                "phone": primary_contact.get("mobile_no"),
            }
        )
    result = customer_doc.add_contacts([contact_name], "HD Customer Manager")
    customer_doc.set_primary(contact_name)
    customer_doc.save()
    return result["invite_result"]["invited_emails"]


@frappe.whitelist()
def delete_customer(name: str, delete_tickets: bool = False) -> None:
    """Delete an HD Customer, either deleting or unlinking its tickets.

    When ``delete_tickets`` is set, every ticket linked to the customer is
    deleted as well. Otherwise the ``customer`` link on those tickets is cleared
    so the tickets are preserved but no longer tied to the deleted customer.
    """
    frappe.has_permission("HD Customer", "delete", throw=True)
    permission = "delete" if delete_tickets else "write"
    frappe.has_permission("HD Ticket", permission, throw=True)
    frappe.delete_doc("HD Customer", name, flags={"delete_tickets": delete_tickets})


@frappe.whitelist()
def get_portal_account() -> dict:
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
            "language",
            "time_zone",
        ],
        as_dict=True,
    )
    return {"user": user, "organizations": _get_organizations()}


@frappe.whitelist()
def get_organization(customer: str) -> dict:
    customer_doc = frappe.get_doc("HD Customer", customer)
    customer_doc.check_permission("read")
    can_manage = _has_manager_permission(customer_doc)
    can_invite = can_manage and frappe.db.get_single_value(
        "HD Settings", "allow_customer_managers_to_invite"
    )
    return {
        "email": customer_doc.email_id,
        "country": customer_doc.country,
        "members": _get_members(customer_doc, include_last_active=can_manage),
        "invitations": _get_invitations(customer_doc) if can_invite else [],
    }


@frappe.whitelist()
def get_invitable_contacts(customer: str, query: str = "") -> list[dict]:
    customer_doc = frappe.get_doc("HD Customer", customer)
    _validate_manager_permission(
        customer_doc,
        "allow_customer_managers_to_invite",
        _("You are not permitted to invite members"),
    )
    domain = (customer_doc.domain or "").strip().lstrip("@").lower()
    # Other organizations' people stay private.
    if not domain or domain in PUBLIC_EMAIL_DOMAINS:
        return []
    Contact = frappe.qb.DocType("Contact")
    Agent = frappe.qb.DocType("HD Agent")
    search = f"%{query.strip()}%"
    q = (
        frappe.qb.from_(Contact)
        .select(Contact.full_name, Contact.email_id.as_("email"), Contact.image)
        .where(Contact.user.isnotnull() & (Contact.user != ""))
        .where(Contact.user.notin(frappe.qb.from_(Agent).select(Agent.name)))
        .where(Contact.full_name.like(search) | Contact.email_id.like(search))
        .where(Contact.email_id.like(f"%@{domain}"))
        .orderby(Contact.full_name)
        .limit(MAX_SUGGESTIONS)
    )
    if members := [row.contact_name for row in customer_doc.contacts]:
        q = q.where(Contact.name.notin(members))
    if invited := [row["email"] for row in customer_doc.list_pending_invitations()]:
        q = q.where(Contact.email_id.notin(invited))
    return q.run(as_dict=True)


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60, ip_based=False, user_based=True)
def invite_members(customer: str, emails: list[str], is_manager: bool) -> dict:
    """Skips silently: the checks span the whole site, not this organization.

    Not `invite_by_email`: its hook role would open Frappe's invite endpoints."""
    customer_doc = frappe.get_doc("HD Customer", customer)
    _validate_manager_permission(
        customer_doc,
        "allow_customer_managers_to_invite",
        _("You are not permitted to invite members"),
    )
    if sbool(is_manager):
        # inviting a manager grants the role, so it needs the manage setting too
        _validate_manager_permission(
            customer_doc,
            "allow_customer_managers_to_manage_organization",
            _("You are not permitted to change member roles"),
        )
    # the db matches case-insensitively; lower both sides so lookups agree
    emails = list(dict.fromkeys(email.strip().lower() for email in emails))
    if len(emails) > MAX_INVITES:
        frappe.throw(_("You can invite up to {0} people at a time").format(MAX_INVITES))
    contact_by_email = {
        email.lower(): name
        for email, name in frappe.get_all(
            "Contact",
            filters={"email_id": ["in", emails]},
            fields=["email_id", "name"],
            as_list=True,
        )
    }
    # accepting would bypass update_member_role for an existing member
    members = {row.contact_name for row in customer_doc.contacts}
    disabled = {
        email.lower()
        for email in frappe.get_all(
            "User", filters={"email": ["in", emails], "enabled": 0}, pluck="email"
        )
    }
    skipped = {
        *(email for email in emails if contact_by_email.get(email) in members),
        *_get_invited_emails(emails, "Accepted"),
        *_get_invited_emails(emails, "Pending"),
    } - disabled
    result = {
        "invited_emails": [e for e in emails if e not in skipped and e not in disabled],
        "skipped_emails": [e for e in emails if e in skipped],
        "disabled_emails": [e for e in emails if e in disabled],
    }
    sent = frappe.db.count(
        "User Invitation",
        {
            "invited_by": frappe.session.user,
            "creation": [">", add_to_date(now_datetime(), hours=-1)],
        },
    )
    if sent + len(result["invited_emails"]) > MAX_INVITES_PER_HOUR:
        frappe.throw(
            _("You can invite up to {0} people an hour").format(MAX_INVITES_PER_HOUR),
            frappe.RateLimitExceededError,
        )
    role = MANAGER_ROLE if sbool(is_manager) else "HD Customer"
    invitations = [
        frappe.get_doc(
            doctype="User Invitation",
            email=email,
            roles=[{"role": role}],
            app_name="helpdesk",
            redirect_to_path=CUSTOMER_PORTAL_ROOT,
            customer=customer_doc.name,
            contact=contact_by_email.get(email),
        )
        for email in result["invited_emails"]
    ]
    # validate all first: each insert mails at once
    for invitation in invitations:
        invitation.validate_invite()
    for invitation in invitations:
        invitation.insert(ignore_permissions=True)
    return result


def _get_invited_emails(emails: list[str], status: str) -> list[str]:
    filters = {"email": ["in", emails], "status": status, "app_name": "helpdesk"}
    if status == "Accepted":
        filters["user"] = ["is", "set"]
    return [
        email.lower()
        for email in frappe.get_all("User Invitation", filters=filters, pluck="email")
    ]


@frappe.whitelist(methods=["POST"])
def update_member_role(customer: str, contact: str, is_manager: bool) -> None:
    customer_doc = frappe.get_doc("HD Customer", customer)
    _validate_manager_permission(
        customer_doc,
        "allow_customer_managers_to_manage_organization",
        _("You are not permitted to change member roles"),
    )
    member = _get_member_row(customer_doc, contact)
    member.is_manager = int(sbool(is_manager))
    customer_doc.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def remove_member(customer: str, contact: str) -> None:
    customer_doc = frappe.get_doc("HD Customer", customer)
    _validate_manager_permission(
        customer_doc,
        "allow_customer_managers_to_manage_organization",
        _("You are not permitted to remove members"),
    )
    _get_member_row(customer_doc, contact)
    customer_doc.remove_contact(contact)
    customer_doc.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def cancel_invitation(customer: str, invitation: str) -> None:
    customer_doc = frappe.get_doc("HD Customer", customer)
    _validate_manager_permission(
        customer_doc,
        "allow_customer_managers_to_invite",
        _("You are not permitted to invite members"),
    )
    user_invitation = frappe.get_doc("User Invitation", invitation)
    if user_invitation.customer != customer_doc.name:
        frappe.throw(
            _("This invitation does not belong to your organization"),
            frappe.PermissionError,
        )
    user_invitation.flags.ignore_permissions = True
    user_invitation.cancel_invite()


@frappe.whitelist(methods=["POST"])
def update_organization_image(customer: str, image: str) -> None:
    customer_doc = frappe.get_doc("HD Customer", customer)
    _validate_manager_permission(
        customer_doc,
        "allow_customer_managers_to_manage_organization",
        _("You are not permitted to change the organization's logo"),
    )
    validate_uploaded_image(image)
    customer_doc.image = image or None
    customer_doc.save(ignore_permissions=True)


def _get_organizations() -> list[dict]:
    session_contact = get_user_contact()
    if not session_contact:
        return []
    memberships = get_customers(contact=session_contact, get_roles=True)
    if not memberships:
        return []
    customer_names = [row["name"] for row in memberships]
    managed_customers = {row["name"] for row in memberships if row["is_manager"]}
    agent_manager = is_agent_manager()
    member_counts = dict(
        frappe.get_all(
            "HD Customer Member",
            filters={"parent": ["in", customer_names]},
            fields=["parent", COUNT_NAME],
            group_by="parent",
            as_list=True,
        )
    )
    ticket_counts = _count_readable_tickets(customer_names)
    rows = frappe.get_all(
        "HD Customer",
        filters={"name": ["in", customer_names]},
        fields=["name", "customer_name", "image", "domain", "primary_contact"],
    )
    organizations = [
        {
            "name": row.name,
            "customer_name": row.customer_name,
            "image": row.image,
            "domain": row.domain,
            # agent managers manage every organization, as in _has_manager_permission
            "role": _get_role(
                row.primary_contact == session_contact,
                row.name in managed_customers or agent_manager,
            ),
            "member_count": member_counts.get(row.name, 0),
            "ticket_count": ticket_counts.get(row.name, 0),
        }
        for row in rows
    ]
    organizations.sort(
        key=lambda organization: (
            ROLE_ORDER[organization["role"]],
            (organization["customer_name"] or "").lower(),
        )
    )
    return organizations


def _get_members(customer_doc, include_last_active: bool) -> list[dict]:
    contact_names = [row.contact_name for row in customer_doc.contacts]
    details = customer_doc.get_contact_details(contact_names)
    last_active = (
        customer_doc.get_last_active(
            [contact.user for contact in details.values() if contact.user]
        )
        if include_last_active
        else {}
    )
    session_contact = get_user_contact()
    members = []
    for row in customer_doc.contacts:
        contact = details.get(row.contact_name)
        if not contact:
            continue
        is_owner = row.contact_name == customer_doc.primary_contact
        member = {
            "contact": row.contact_name,
            "full_name": contact.full_name,
            "email": contact.email_id,
            "image": contact.image,
            "role": _get_role(is_owner, row.is_manager),
            "is_you": row.contact_name == session_contact,
        }
        if include_last_active:
            member["last_active"] = last_active.get(contact.user)
        members.append(member)
    # the caller first, then by role
    members.sort(
        key=lambda member: (
            not member["is_you"],
            ROLE_ORDER[member["role"]],
            (member["full_name"] or "").lower(),
        )
    )
    return members


def _get_invitations(customer_doc) -> list[dict]:
    return [
        {
            "name": invitation["name"],
            "email": invitation["email"],
            "role": _get_role(False, MANAGER_ROLE in invitation["roles"]),
            "invited_by": get_fullname(invitation["invited_by"]),
            "invited_by_you": invitation["invited_by"] == frappe.session.user,
            "invited_on": invitation["invited_on"],
        }
        for invitation in customer_doc.list_pending_invitations()
    ]


def _get_role(is_owner: bool, is_manager: bool) -> str:
    return "Owner" if is_owner else "Manager" if is_manager else "Member"


def _count_readable_tickets(customers: list[str]) -> dict[str, int]:
    """get_list: a member counts only their own tickets."""
    rows = frappe.get_list(
        "HD Ticket",
        filters={"customer": ["in", customers]},
        fields=["customer", COUNT_NAME],
        group_by="customer",
    )
    return {row.customer: row["count"] for row in rows}


def _validate_manager_permission(customer_doc, setting: str, message: str) -> None:
    if not frappe.db.get_single_value("HD Settings", setting):
        frappe.throw(message, frappe.PermissionError)
    if not _has_manager_permission(customer_doc):
        frappe.throw(
            _("You are not permitted to manage {0}").format(customer_doc.customer_name),
            frappe.PermissionError,
        )


def _has_manager_permission(customer_doc) -> bool:
    return is_agent_manager() or is_customer_manager(customer_doc.name)


def _get_member_row(customer_doc, contact: str):
    if contact == customer_doc.primary_contact:
        frappe.throw(_("Role of primary contact cannot be changed"))
    if contact == get_user_contact():
        frappe.throw(_("You cannot change your own role"))
    member = next(
        (row for row in customer_doc.contacts if row.contact_name == contact), None
    )
    if not member:
        frappe.throw(_("{0} is not a member of {1}").format(contact, customer_doc.name))
    return member
