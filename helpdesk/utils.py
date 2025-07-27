import functools
import re
from typing import List

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.model.document import Document
from frappe.realtime import get_website_room
from frappe.utils.safe_exec import get_safe_globals
from frappe.utils.telemetry import capture as _capture
from pypika import Criterion


def check_permissions(doctype, parent, doc=None):
    user = frappe.session.user

    permissions = ("select", "read")
    has_select_permission, has_read_permission = [
        frappe.has_permission(doctype, perm, user=user, doc=doc, parent_doctype=parent)
        for perm in permissions
    ]

    if not has_select_permission and not has_read_permission:
        frappe.throw(
            _("Insufficient Permission for {0}").format(doctype), frappe.PermissionError
        )


def is_admin(user: str = None) -> bool:
    """
    Check whether `user` is an admin

    :param user: User to check against, defaults to current user
    :return: Whether `user` is an admin
    """
    user = user or frappe.session.user
    return user == "Administrator"


def is_agent(user: str = None) -> bool:
    """
    Check whether `user` is an agent

    :param user: User to check against, defaults to current user
    :return: Whether `user` is an agent
    """
    user = user or frappe.session.user
    return (
        is_admin()
        or "Agent Manager" in frappe.get_roles(user)
        or "Agent" in frappe.get_roles(user)
        or bool(frappe.db.exists("HD Agent", {"name": user}))
    )


def publish_event(event: str, data: dict, user: str = None):
    """
    Publish `event` to a room with `data`

    :param event: Event name. Example: "refetch_resource"
    :param data: Data to be sent with the event
    :param user: User to send the event to, defaults to current user
    """
    room = get_website_room()
    user = user or frappe.session.user
    frappe.publish_realtime(
        event, message=data, room=room, after_commit=True, user=user
    )


def refetch_resource(key: str | List[str], user=None):
    event = "refetch_resource"
    data = {"cache_key": key}
    publish_event(event, data, user=user)


def capture_event(event: str):
    return _capture(event, "helpdesk")


def get_customer(contact: str) -> tuple[str]:
    """
    Get `Customer` from `Contact`

    :param contact: Contact which belongs to a customer
    :return: Customer `name` if available
    """
    QBDynamicLink = frappe.qb.DocType("Dynamic Link")
    QBContact = frappe.qb.DocType("Contact")
    conditions = [QBDynamicLink.parent == contact, QBContact.email_id == contact]
    return [
        i[0]
        for i in (
            frappe.qb.from_(QBDynamicLink)
            .select(QBDynamicLink.link_name)
            .where(QBDynamicLink.parentfield == "links")
            .where(QBDynamicLink.parenttype == "Contact")
            .where(QBDynamicLink.link_doctype == "HD Customer")
            .join(QBContact)
            .on(QBDynamicLink.parent == QBContact.name)
            .where(Criterion.any(conditions))
            .run()
        )
    ]


def extract_mentions(html):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    mentions = []
    for d in soup.find_all("span", attrs={"data-type": "mention"}):
        mentions.append(
            frappe._dict(full_name=d.get("data-label"), email=d.get("data-id"))
        )
    return mentions


def alphanumeric_to_int(s: str) -> int | None:
    """
    Get int from alphanumeric string, using regex
    String example: "foo-123" -> 123


    :param s: Alphanumeric string to be searched for
    :return: Integer if a number is found
    """
    s = re.search(r"\d+", s)

    if not s:
        return

    return int(s.group(0))


def get_context(d: Document) -> dict:
    """
    Get safe context for `safe_eval`

    :param doc: `Document` to add in context
    :return: Context with `doc` and safe variables
    """
    utils = get_safe_globals().get("frappe").get("utils")
    return {
        "doc": d.as_dict(),
        "frappe": frappe._dict(utils=utils),
    }


def agent_only(fn):
    """Decorator to validate if user is an agent."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_agent():
            frappe.throw(
                msg=_("You are not permitted to access this resource."),
                title=_("Not Allowed"),
                exc=frappe.PermissionError,
            )

        return fn(*args, **kwargs)

    return wrapper


def get_agents_team():
    QBTeam = frappe.qb.DocType("HD Team")
    QBTeamMember = frappe.qb.DocType("HD Team Member")

    teams = (
        frappe.qb.from_(QBTeamMember)
        .where(QBTeamMember.user == frappe.session.user)
        .join(QBTeam)
        .on(QBTeam.name == QBTeamMember.parent)
        .select(QBTeam.team_name, QBTeam.ignore_restrictions)
        .run(as_dict=True)
    )
    return teams


contact_default_columns = [
    {
        "label": "Name",
        "type": "Data",
        "key": "full_name",
        "width": "17rem",
    },
    {
        "label": "Email",
        "type": "Data",
        "key": "email_id",
        "width": "24rem",
    },
    {
        "label": "Created On",
        "type": "Datetime",
        "key": "creation",
        "width": "8rem",
    },
]
