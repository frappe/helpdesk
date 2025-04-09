import frappe
from frappe import _
from frappe.utils import get_user_info_for_avatar
from frappe.utils.caching import redis_cache
from pypika import Criterion, Order

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.helpdesk.doctype.hd_form_script.hd_form_script import get_form_script
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_fields_meta
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_one as get_template
from helpdesk.utils import agent_only, check_permissions, get_customer, is_agent


@frappe.whitelist()
# flake8: noqa
def new(doc, attachments=[]):
    doc["doctype"] = "HD Ticket"
    doc["via_customer_portal"] = bool(frappe.session.user)
    doc["attachments"] = attachments
    d = frappe.get_doc(doc).insert()
    return d


@frappe.whitelist()
def get_one(name, is_customer_portal=False):
    check_permissions("HD Ticket", None)
    QBContact = frappe.qb.DocType("Contact")
    QBTicket = frappe.qb.DocType("HD Ticket")

    _is_agent = is_agent()

    query = (
        frappe.qb.from_(QBTicket)
        .select(QBTicket.star)
        .where(QBTicket.name == name)
        .limit(1)
    )

    if not _is_agent:
        query = query.where(get_customer_criteria())

    ticket = query.run(as_dict=True)
    if not len(ticket):
        frappe.throw(_("Ticket not found"), frappe.DoesNotExistError)
    ticket = ticket.pop()

    contact = (
        frappe.qb.from_(QBContact)
        .select(
            QBContact.company_name,
            QBContact.email_id,
            QBContact.image,
            QBContact.mobile_no,
            QBContact.name,
            QBContact.phone,
        )
        .where(QBContact.name == ticket.contact)
        .run(as_dict=True)
    )
    if contact:
        contact = contact[0]
    else:
        contact = {
            "email_id": ticket.raised_by,
            "name": ticket.raised_by.split("@")[0],
        }
    template = ticket.template or DEFAULT_TICKET_TEMPLATE
    return {
        **ticket,
        "comments": get_comments(name),
        "communications": get_communications(name),
        "contact": contact,
        "history": get_history(name),
        "tags": get_tags(name),
        "template": get_template(template),
        "views": get_views(name),
        "_form_script": get_form_script(
            "HD Ticket", is_customer_portal=is_customer_portal
        ),
        "fields": get_meta(template),
    }


def get_meta(template: str):
    default_fields = ["ticket_type", "agent_group", "priority", "customer"]
    DocField = frappe.qb.DocType("DocField")

    fields = (
        frappe.qb.from_(DocField)
        .select(DocField.star)
        .where(DocField.parent == "HD Ticket")
        .where(DocField.fieldname.isin(default_fields))
        .run(as_dict=True)
    )
    meta_fields = get_fields_meta(template)
    meta_fields = [f for f in meta_fields if f["fieldname"] not in default_fields]

    fields.extend(meta_fields)
    return fields


def get_customer_criteria():
    QBTicket = frappe.qb.DocType("HD Ticket")
    user = frappe.session.user
    conditions = [
        QBTicket.contact == user,
        QBTicket.raised_by == user,
    ]
    customer = get_customer(user)
    for c in customer:
        conditions.append(QBTicket.customer == c)
    return Criterion.any(conditions)


def get_assignee(_assign: str):
    j = frappe.parse_json(_assign)
    if not j or len(j) < 1:
        return
    return get_user_info_for_avatar(j.pop())


def get_communications(ticket: str):
    QBCommunication = frappe.qb.DocType("Communication")
    communications = (
        frappe.qb.from_(QBCommunication)
        .select(
            QBCommunication.bcc,
            QBCommunication.cc,
            QBCommunication.content,
            QBCommunication.creation,
            QBCommunication.name,
            QBCommunication.sender,
            QBCommunication.recipients,
            QBCommunication.subject,
        )
        .where(QBCommunication.reference_doctype == "HD Ticket")
        .where(QBCommunication.reference_name == ticket)
        .orderby(QBCommunication.creation, order=Order.asc)
        .run(as_dict=True)
    )
    for c in communications:
        c.attachments = get_attachments("Communication", c.name)
        c.user = get_user_info_for_avatar(c.sender)
    return communications


def get_comments(ticket: str):
    if not frappe.has_permission("HD Ticket Comment", "read"):
        return []
    QBComment = frappe.qb.DocType("HD Ticket Comment")
    comments = (
        frappe.qb.from_(QBComment)
        .select(
            QBComment.commented_by,
            QBComment.content,
            QBComment.creation,
            QBComment.is_pinned,
            QBComment.name,
        )
        .where(QBComment.reference_ticket == ticket)
        .orderby(QBComment.creation, order=Order.asc)
        .run(as_dict=True)
    )
    for c in comments:
        c.user = get_user_info_for_avatar(c.commented_by)
        c.attachments = get_attachments("HD Ticket Comment", c.name)
    return comments


def get_history(ticket: str):
    if not frappe.has_permission("HD Ticket Activity", "read"):
        return []
    QBActivity = frappe.qb.DocType("HD Ticket Activity")
    history = (
        frappe.qb.from_(QBActivity)
        .select(
            QBActivity.name, QBActivity.action, QBActivity.owner, QBActivity.creation
        )
        .where(QBActivity.ticket == ticket)
        .orderby(QBActivity.creation, order=Order.desc)
    )
    history = history.run(as_dict=True)
    for h in history:
        h.user = get_user_info_for_avatar(h.owner)
    return history


def get_views(ticket: str):
    QBViewLog = frappe.qb.DocType("View Log")
    views = (
        frappe.qb.from_(QBViewLog)
        .select(
            QBViewLog.creation,
            QBViewLog.name,
            QBViewLog.viewed_by,
        )
        .where(QBViewLog.reference_doctype == "HD Ticket")
        .where(QBViewLog.reference_name == ticket)
        .orderby(QBViewLog.creation, order=Order.desc)
        .run(as_dict=True)
    )
    for v in views:
        v.user = get_user_info_for_avatar(v.viewed_by)
    return views


def get_tags(ticket: str):
    QBTag = frappe.qb.DocType("Tag Link")
    rows = (
        frappe.qb.from_(QBTag)
        .select(QBTag.tag)
        .where(QBTag.document_type == "HD Ticket")
        .where(QBTag.document_name == ticket)
        .orderby(QBTag.creation, order=Order.asc)
        .run(as_dict=True)
    )
    res = []
    for tag in rows:
        res.append(tag.tag)
    return res


@redis_cache()
def get_attachments(doctype, name):
    QBFile = frappe.qb.DocType("File")

    return (
        frappe.qb.from_(QBFile)
        .select(QBFile.name, QBFile.file_url, QBFile.file_name)
        .where(QBFile.attached_to_doctype == doctype)
        .where(QBFile.attached_to_name == name)
        .run(as_dict=True)
    )


@frappe.whitelist()
@agent_only
def merge_ticket(source: int, target: int):
    # check if source and target exists
    if not frappe.db.exists("HD Ticket", source):
        frappe.throw(_("Source ticket does not exist"))
    if not frappe.db.exists("HD Ticket", target):
        frappe.throw(_("Target ticket does not exist"))
    if source == target:
        frappe.throw(_("Source and target ticket cannot be same"))

    source_comments = frappe.db.get_list(
        "HD Ticket Comment", filters={"reference_ticket": source}, pluck="name"
    )
    duplicate_list_retain_timestamp("HD Ticket Comment", source_comments, target)

    source_communications = frappe.db.get_list(
        "Communication",
        filters={"reference_doctype": "HD Ticket", "reference_name": source},
        pluck="name",
    )
    duplicate_list_retain_timestamp("Communication", source_communications, target)

    source_attachments = frappe.db.get_list(
        "File", filters={"attached_to_doctype": "HD Ticket", "attached_to_name": source}
    )
    duplicate_list_retain_timestamp(source_attachments, target)

    frappe.db.set_value(
        "HD Ticket",
        source,
        {
            "status": "Closed",
            "is_merged": 1,
            "merged_with": target,
        },
    )
    # create comment on target ticket that source ticket is merged with target ticket
    # create communication on target ticket that source ticket is merged with target ticket

    return _("Ticket {0} merged with {1}", source, target)


def duplicate_list_retain_timestamp(doctype, activities: list, target: int):
    for activity in activities:
        original_doc = frappe.get_doc(doctype, activity)

        duplicate_doc = frappe.copy_doc(original_doc)

        if doctype == "Communication":
            duplicate_doc.reference_name = target
        elif doctype == "HD Ticket Comment":
            duplicate_doc.reference_ticket = target
        elif doctype == "File":
            duplicate_doc.attached_to_name = target

        duplicate_doc.insert(ignore_permissions=True)

        frappe.db.set_value(
            duplicate_doc.doctype,
            duplicate_doc.name,
            {
                "creation": original_doc.creation,
                "modified": original_doc.modified,
                "owner": original_doc.owner,
                "modified_by": original_doc.modified_by,
            },
            update_modified=False,
        )
