from urllib.parse import quote

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_name
from frappe.core.api.user_invitation import invite_by_email
from frappe.email.doctype.email_account.email_account import EmailAccount
from frappe.rate_limiter import rate_limit
from frappe.utils import (
    add_to_date,
    escape_html,
    get_url,
    now_datetime,
    strip_html_tags,
    validate_email_address,
)

from helpdesk.utils import CUSTOMER_PORTAL_ROOT, agent_only, is_admin

# ponytail: fixed site-wide cap, an HD Settings field if a site needs to tune it
GUEST_TICKETS_PER_HOUR = 100
GUEST_DRAFT_SECONDS = 3 * 24 * 60 * 60
CONTINUE_EMAIL_COOLDOWN_SECONDS = 10 * 60


@frappe.whitelist()
@agent_only
def bulk_reply(ticket_ids: list, message: str, attachments: list | None = None):

    if not ticket_ids:
        return

    # dedupe but keep the order the agent picked. set() orders by hash, which varies
    # per process, and duplicates would attach the same file to a ticket twice
    ticket_ids = list(dict.fromkeys(ticket_ids))

    # Check every ticket before writing anything, so one ticket the agent cannot
    # reply to does not leave the rest of the batch half done
    tickets = []
    for ticket_id in ticket_ids:
        frappe.has_permission("HD Ticket", "write", doc=ticket_id, throw=True)
        tickets.append(frappe.get_doc("HD Ticket", ticket_id))

    link_attachments_to_tickets(attachments, ticket_ids)

    for doc in tickets:
        try:
            doc.reply_via_agent(
                message, to=doc.raised_by, attachments=attachments or []
            )
        except Exception as e:
            frappe.log_error(
                title=f"Bulk reply failed for ticket {doc.name}",
                message=str(e),
            )


def link_attachments_to_tickets(attachments: list | None, ticket_ids: list):
    if not attachments:
        return
    if not ticket_ids:
        return

    # only one attachment is created, but does not refer to any doctype/docname until now. Link it to all the tickets in context.
    # Done because, FileUploader only handles for one file, and cant upload to multiple doctypes/docnames at the same time.
    for a in attachments:
        file_doc = frappe.get_doc("File", a)
        file_doc.attached_to_doctype = "HD Ticket"
        file_doc.attached_to_name = ticket_ids[0]
        file_doc.save()

    for ticket_id in ticket_ids[1:]:
        for a in attachments:
            file_doc = frappe.get_doc("File", a)
            new_file_doc = frappe.copy_doc(file_doc)
            new_file_doc.attached_to_name = ticket_id
            new_file_doc.save()


def assign_ticket_to_agent(ticket_id, agent_id=None):
    if not ticket_id:
        return

    ticket_doc = frappe.get_doc("HD Ticket", ticket_id)

    if not agent_id:
        # assign to self
        agent_id = frappe.session.user

    if not frappe.db.exists("HD Agent", agent_id):
        frappe.throw(_("Tickets can only be assigned to agents"))

    ticket_doc.assign_agent(agent_id)
    return ticket_doc


@frappe.whitelist()
def delete_ticket(name: str):
    if not is_admin():
        frappe.throw(
            msg=_("Only administrators can delete tickets."),
            title=_("Not Allowed"),
            exc=frappe.PermissionError,
        )
    frappe.delete_doc("HD Ticket", name, force=True, ignore_permissions=True)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def new_guest_ticket(
    subject: str, description: str, email: str, first_name: str | None = None
) -> None:
    """A signed-out visitor's ticket; only these fields reach it, the rest are HD Ticket's defaults."""
    if not frappe.db.get_single_value("HD Settings", "allow_anyone_to_create_tickets"):
        frappe.throw(_("Sign in to raise a ticket"), frappe.PermissionError)

    email = (email or "").strip().lower()
    validate_email_address(email, throw=True)
    subject = (subject or "").strip()
    # The editor's empty value is `<p></p>`, not "".
    if not subject or not strip_html_tags(description or "").strip():
        frappe.throw(_("Subject and description are required"))
    if frappe.db.exists("Email Account", {"email_id": email}):
        frappe.throw(_("Please use your own email address"))
    if guest_tickets_in_last_hour() >= GUEST_TICKETS_PER_HOUR:
        frappe.throw(
            _("We're getting a lot of requests. Please try again in an hour."),
            frappe.RateLimitExceededError,
        )

    # Nothing is returned either way, so the form never tells who has an account.
    if frappe.db.exists("User", {"email": email, "enabled": 1}) and (
        EmailAccount.find_outgoing()
    ):
        send_continue_email(email, subject, description)
        return

    ensure_contact(email, first_name)
    # `set_contact` links the Contact by email; the toggle's Guest rule allows the insert.
    ticket = frappe.get_doc(
        {
            "doctype": "HD Ticket",
            "subject": subject,
            "description": description,
            "raised_by": email,
        }
    ).insert()
    invite_requester(ticket)


def guest_tickets_in_last_hour() -> int:
    return frappe.db.count(
        "HD Ticket",
        {"owner": "Guest", "creation": (">", add_to_date(now_datetime(), hours=-1))},
    )


def ensure_contact(email: str, first_name: str | None) -> None:
    if get_contact_name(email):
        return
    contact = frappe.get_doc(
        {
            "doctype": "Contact",
            "first_name": escape_html((first_name or "").strip()) or email,
        }
    )
    contact.append("email_ids", {"email_id": email, "is_primary": True})
    # Guest has no Contact rights; the toggle checked above is the permission.
    contact.insert(ignore_permissions=True)


def invite_requester(ticket) -> None:
    """Ask a new requester to take an account, so they can follow the ticket."""
    # An existing account, even a disabled one, must not be handed HD Customer by an invite.
    if frappe.db.exists("User", {"email": ticket.raised_by}):
        return
    # Queued: the invite's mail flushes on commit, and a dead mail server must not fail the ticket.
    frappe.enqueue(
        send_requester_invite,
        queue="short",
        now=frappe.flags.in_test,
        ticket_name=ticket.name,
        email=ticket.raised_by,
        contact=ticket.contact,
    )


def send_requester_invite(ticket_name: str, email: str, contact: str | None) -> None:
    # User Invitation only accepts an inviter with an agent or manager role.
    frappe.set_user("Administrator")
    invite_by_email(
        emails=email,
        roles=["HD Customer"],
        redirect_to_path=f"{CUSTOMER_PORTAL_ROOT}/tickets/{ticket_name}",
        app_name="helpdesk",
        contact=contact,
    )


def send_continue_email(email: str, subject: str, description: str) -> None:
    """Email an account holder a sign-in link that brings back what they wrote."""
    # One per address per cooldown, so a stranger cannot flood someone's inbox.
    cooldown_key = f"hd_guest_continue:{email}"
    if frappe.cache.get_value(cooldown_key):
        return
    frappe.cache.set_value(
        cooldown_key, 1, expires_in_sec=CONTINUE_EMAIL_COOLDOWN_SECONDS
    )

    token = frappe.generate_hash(length=32)
    frappe.cache.set_value(
        f"hd_guest_draft:{token}",
        {"email": email, "subject": subject, "description": description},
        expires_in_sec=GUEST_DRAFT_SECONDS,
    )
    form = f"{CUSTOMER_PORTAL_ROOT}/tickets/new?draft={token}"
    frappe.sendmail(
        recipients=email,
        subject=_("Continue your request"),
        template="continue_guest_request",
        args={"link": get_url(f"/login?redirect-to={quote(form, safe='')}")},
    )


@frappe.whitelist(methods=["POST"])
def get_guest_draft(token: str) -> dict | None:
    """What a guest wrote before being asked to sign in: once, and only to that email's account."""
    key = f"hd_guest_draft:{token}"
    draft = frappe.cache.get_value(key)
    if not draft or draft["email"] != frappe.db.get_value(
        "User", frappe.session.user, "email"
    ):
        return None
    frappe.cache.delete_value(key)
    return {"subject": draft["subject"], "description": draft["description"]}
