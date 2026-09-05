"""Customer-portal settings API.

Backs the settings modal on the Studio-built portal pages. Portal users have no
role permissions on Contact or User Invitation, so member details are resolved
here, scoped to the caller's own organization (HD Customer membership).
"""

import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils import sbool

from helpdesk.utils import get_customers, is_agent

# The organizations you can act on come first; alphabetical within a role.
ROLE_ORDER = {"Owner": 0, "Manager": 1, "Member": 2}


@frappe.whitelist()
def get_settings() -> dict:
    """The session user's profile plus every organization they belong to.

    A contact can be a member of several HD Customers, so this lists them all and
    the portal drills into one at a time via `get_organization`.
    """
    user = frappe.get_doc("User", frappe.session.user)
    return {
        "user": {
            "name": user.name,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "full_name": user.full_name,
            "image": user.user_image,
        },
        "is_agent": is_agent(),
        "organizations": get_organizations(),
    }


def get_organizations() -> list[dict]:
    """Every organization the session user belongs to, with their role in each."""
    memberships = get_customers(get_roles=True)
    if not memberships:
        return []

    rows = frappe.get_all(
        "HD Customer",
        filters={"name": ["in", [membership["name"] for membership in memberships]]},
        fields=[
            "name",
            "customer_name",
            "image",
            "domain",
            "email_id",
            "owner",
            "primary_contact",
        ],
    )
    by_name = {row.name: row for row in rows}
    you = own_contact()
    members = count_by(
        "HD Customer Member", "parent", list(by_name), parenttype="HD Customer"
    )
    # Every ticket the organization has raised, not only the ones still open: the card
    # says how much history there is with them, and an organization whose tickets are all
    # answered is not one with nothing on file.
    tickets = count_by("HD Ticket", "customer", list(by_name))

    organizations = []
    for membership in memberships:
        row = by_name.get(membership["name"])
        if not row:
            continue
        organizations.append(
            {
                "name": row.name,
                "customer_name": row.customer_name,
                "image": row.image,
                "domain": row.domain,
                "email": row.email_id or row.owner,
                "is_manager": bool(membership.get("is_manager")),
                "role": describe_role(row, membership, you),
                "member_count": members.get(row.name, 0),
                "ticket_count": tickets.get(row.name, 0),
            }
        )
    organizations.sort(
        key=lambda org: (
            ROLE_ORDER.get(org["role"], len(ROLE_ORDER)),
            (org["customer_name"] or org["name"]).lower(),
        )
    )
    return organizations


def describe_role(row, membership: dict, contact: str | None) -> str:
    """The caller's standing in one organization.

    Owner is the primary contact, whom HD Customer keeps a manager, so the three
    labels are a hierarchy rather than independent flags.
    """
    if contact and row.primary_contact == contact:
        return "Owner"
    return "Manager" if membership.get("is_manager") else "Member"


def count_by(
    doctype: str, fieldname: str, values: list[str], **equals
) -> dict[str, int]:
    """Rows of `doctype` per value of `fieldname`, grouped in SQL rather than fetched.

    Skips permission filters deliberately: the caller has already narrowed `values`
    to organizations the session user belongs to.
    """
    if not values:
        return {}
    table = frappe.qb.DocType(doctype)
    query = (
        frappe.qb.from_(table)
        .select(table[fieldname], Count(table.name).as_("total"))
        .where(table[fieldname].isin(values))
        .groupby(table[fieldname])
    )
    for name, value in equals.items():
        query = query.where(table[name] == value)
    return {row[fieldname]: row.total for row in query.run(as_dict=True)}


@frappe.whitelist()
def get_organization(customer: str) -> dict:
    """One organization the caller belongs to, with its members if they manage it."""
    membership = get_membership(customer)
    if not membership:
        frappe.throw(
            _("You are not a member of {0}").format(customer), frappe.PermissionError
        )

    doc = frappe.get_doc("HD Customer", customer)
    is_manager = bool(membership.get("is_manager"))
    return {
        "name": doc.name,
        "customer_name": doc.customer_name,
        "image": doc.image,
        "domain": doc.domain,
        "email": doc.email_id or doc.owner,
        "country": doc.country,
        "is_manager": is_manager,
        # Anyone in the organization may see who else is in it; only a manager can
        # change it. Resolved here because portal users hold no Contact permissions.
        "members": get_members(doc),
    }


def get_membership(customer: str) -> dict | None:
    """The session user's membership row for `customer`, or None if they have none."""
    for membership in get_customers(get_roles=True):
        if membership["name"] == customer:
            return membership
    return None


def get_managed_customer(customer: str):
    """The named HD Customer, asserting the caller manages *that* organization.

    Every mutation resolves its target through here. Taking the name explicitly is
    what keeps a manager of one organization from acting on another.
    """
    membership = get_membership(customer)
    if not membership or not membership.get("is_manager"):
        frappe.throw(
            _("You are not a manager of {0}").format(customer), frappe.PermissionError
        )
    return frappe.get_doc("HD Customer", customer)


def assert_portal_allows(setting: str) -> None:
    """Manager standing is necessary but not sufficient — the helpdesk must also allow it.

    Paired with `get_managed_customer`: that answers "may this caller act on this
    organization", this answers "is customer-side self-service switched on at all".
    """
    if not frappe.db.get_single_value("HD Settings", setting):
        frappe.throw(_("Your helpdesk does not allow this"), frappe.PermissionError)


def own_contact() -> str | None:
    """The session user's own Contact — the membership they must not act on."""
    return frappe.db.get_value("Contact", {"user": frappe.session.user})


def get_members(customer) -> list[dict]:
    """Active members (from the contacts table) followed by pending invites."""
    you = own_contact()
    contact_names = [row.contact_name for row in customer.contacts]
    details = {}
    if contact_names:
        rows = frappe.get_all(
            "Contact",
            filters={"name": ["in", contact_names]},
            fields=["name", "full_name", "email_id", "image", "user"],
        )
        details = {row.name: row for row in rows}
    last_active = get_last_active(details.values())

    members = []
    for row in customer.contacts:
        info = details.get(row.contact_name)
        members.append(
            {
                "contact": row.contact_name,
                "full_name": (info and info.full_name) or row.contact_name,
                "email": info and info.email_id,
                "image": info and info.image,
                "is_manager": bool(row.is_manager),
                "is_owner": row.contact_name == customer.primary_contact,
                "is_you": row.contact_name == you,
                "last_seen": info and last_active.get(info.user),
                "pending": False,
            }
        )
    members.sort(
        key=lambda member: (
            not member["is_owner"],
            not member["is_manager"],
            (member["full_name"] or "").lower(),
        )
    )
    return members + get_pending_members(customer.name)


def get_last_active(contacts) -> dict:
    """`User.last_active` per linked user, the way `contact.get_contact_info` reads it.

    A contact with no user has never signed in, so it never appears here.
    """
    users = [contact.user for contact in contacts if contact.user]
    if not users:
        return {}
    rows = frappe.get_all(
        "User", filters={"name": ["in", users]}, fields=["name", "last_active"]
    )
    return {row.name: row.last_active for row in rows}


def get_pending_members(customer_name: str) -> list[dict]:
    invites = frappe.get_all(
        "User Invitation",
        filters={
            "app_name": "helpdesk",
            "status": "Pending",
            "customer": customer_name,
        },
        fields=["name", "email", "creation"],
    )
    pending = []
    for invite in invites:
        roles = frappe.get_all(
            "User Role",
            filters={"parent": invite.name, "parenttype": "User Invitation"},
            pluck="role",
        )
        pending.append(
            {
                "invitation": invite.name,
                "contact": None,
                "full_name": invite.email.split("@")[0],
                "email": invite.email,
                "image": None,
                "is_manager": "HD Customer Manager" in roles,
                "is_owner": False,
                "is_you": False,
                # Nobody has signed in on an invitation that is still pending.
                "last_seen": None,
                "pending": True,
            }
        )
    return pending


@frappe.whitelist()
def get_invitable_contacts(customer: str) -> list[dict]:
    """Who this organization can still be asked to add, as the agent desk offers them.

    The same set `InviteContactDialog.vue` builds: contacts that already have a user,
    minus the agents (an agent is not somebody's customer contact), minus whoever is a
    member or holds a pending invite here. It was scoped to the organization's own email
    domain, which suggested nobody unless a customer's `domain` happened to match the
    addresses its people actually use.
    """
    doc = get_managed_customer(customer)
    members = {row.contact_name for row in doc.contacts}
    invited = {member["email"] for member in get_pending_members(doc.name)}
    invited.update(frappe.get_all("HD Agent", pluck="name"))
    rows = frappe.get_all(
        "Contact",
        filters={"user": ["is", "set"]},
        fields=["name", "full_name", "email_id", "image"],
        order_by="full_name asc",
    )
    return [
        {
            "contact": row.name,
            "full_name": row.full_name or row.email_id,
            "email": row.email_id,
            "image": row.image,
        }
        for row in rows
        if row.name not in members and row.email_id not in invited
    ]


@frappe.whitelist()
def update_profile(
    first_name: str | None = None,
    last_name: str | None = None,
    image: str | None = None,
) -> dict:
    """Update the session user's own profile. Deliberately limited to these fields."""
    user = frappe.get_doc("User", frappe.session.user)
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if image is not None:
        user.user_image = image or None
    user.save(ignore_permissions=True)
    sync_contact(user)
    return {"full_name": user.full_name, "image": user.user_image}


def sync_contact(user) -> None:
    """Mirror profile changes onto the linked Contact so member lists stay current."""
    contact_name = frappe.db.get_value("Contact", {"user": user.name})
    if not contact_name:
        return
    contact = frappe.get_doc("Contact", contact_name)
    contact.first_name = user.first_name
    contact.last_name = user.last_name
    contact.image = user.user_image
    contact.save(ignore_permissions=True)


@frappe.whitelist()
def update_member_role(customer: str, contact: str, is_manager: bool) -> None:
    """Toggle a member between manager and member in an organization you manage."""
    assert_portal_allows("allow_customer_managers_to_invite")
    customer = get_managed_customer(customer)
    if contact == customer.primary_contact:
        frappe.throw(_("The owner's role cannot be changed"))
    # demoting yourself would revoke the very rights this call needs
    if contact == own_contact():
        frappe.throw(_("You cannot change your own role"))
    row = next((row for row in customer.contacts if row.contact_name == contact), None)
    if not row:
        frappe.throw(_("{0} is not a member of {1}").format(contact, customer.name))
    row.is_manager = int(sbool(is_manager))
    customer.save()  # role sync happens in HD Customer.before_save


@frappe.whitelist()
def remove_member(customer: str, contact: str) -> None:
    """Remove a member from an organization you manage."""
    assert_portal_allows("allow_customer_managers_to_invite")
    customer = get_managed_customer(customer)
    if contact == customer.primary_contact:
        frappe.throw(_("The owner cannot be removed"))
    if contact == own_contact():
        frappe.throw(_("You cannot remove yourself from the organization"))
    if not any(row.contact_name == contact for row in customer.contacts):
        frappe.throw(_("{0} is not a member of {1}").format(contact, customer.name))
    customer.remove_contact(contact)
    customer.save()


@frappe.whitelist()
def cancel_invitation(customer: str, invitation: str) -> None:
    """Cancel a pending invitation belonging to an organization you manage."""
    assert_portal_allows("allow_customer_managers_to_invite")
    customer = get_managed_customer(customer)
    invitation_doc = frappe.get_doc("User Invitation", invitation)
    if invitation_doc.customer != customer.name:
        frappe.throw(
            _("This invitation does not belong to your organization"),
            frappe.PermissionError,
        )
    invitation_doc.flags.ignore_permissions = True
    invitation_doc.cancel_invite()


@frappe.whitelist()
def update_organization(
    customer: str,
    customer_name: str | None = None,
    image: str | None = None,
) -> str:
    """Update the name or logo of an organization you manage."""
    assert_portal_allows("allow_customer_managers_to_edit_organization")
    customer = get_managed_customer(customer)
    if image is not None:
        customer.image = image or None
    customer.save()
    if customer_name and customer_name != customer.name:
        return frappe.rename_doc("HD Customer", customer.name, customer_name)
    return customer.name
