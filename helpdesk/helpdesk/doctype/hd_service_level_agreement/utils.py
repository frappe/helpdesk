import frappe
from frappe.model.document import Document
from frappe.query_builder import JoinType
from frappe.utils import now_datetime
from pypika import Criterion

from helpdesk.utils import get_context

DOCTYPE = "HD Service Level Agreement"


def get_sla(ticket: Document) -> Document:
    """
    Get Service Level Agreement for `ticket`

    :param doc: Ticket to use
    :return: Applicable SLA
    """
    QBSla = frappe.qb.DocType(DOCTYPE)
    QBPriority = frappe.qb.DocType("HD Service Level Priority")
    now = now_datetime()
    priority = ticket.priority
    q = (
        frappe.qb.from_(QBSla)
        .select(QBSla.name, QBSla.condition)
        .where(QBSla.enabled == True)
        .where(QBSla.default_sla == False)
        .where(Criterion.any([QBSla.start_date.isnull(), QBSla.start_date <= now]))
        .where(Criterion.any([QBSla.end_date.isnull(), QBSla.end_date >= now]))
    )
    if priority:
        q = (
            q.join(QBPriority, JoinType.inner)
            .on(QBPriority.parent == QBSla.name)
            .where(QBPriority.priority == priority)
        )
    sla_list = q.run(as_dict=True)
    res = None
    for sla in sla_list:
        cond = sla.get("condition")
        if not cond or frappe.safe_eval(cond, None, get_context(ticket)):
            res = sla
            break
    return res or get_default()


def get_default() -> Document:
    """
    Get default Service Level Agreement

    :return: Default SLA
    """
    return frappe.get_last_doc(
        DOCTYPE,
        filters={
            "enabled": True,
            "default_sla": True,
        },
    )


def convert_to_seconds(time):
    """
    Convert time string to seconds.

    :param time: Time in datetime object
    :return: Time in seconds
    """
    if not time:
        return 0
    time = time.hour * 3600 + time.minute * 60 + time.second
    return time if time else 0
