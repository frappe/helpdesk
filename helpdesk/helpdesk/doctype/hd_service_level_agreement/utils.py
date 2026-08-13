import frappe
from frappe.model.document import Document
from frappe.query_builder import JoinType
from frappe.utils import now_datetime
from pypika import Criterion

from helpdesk.utils import get_context

DOCTYPE = "HD Service Level Agreement"


def get_sla(ticket: Document) -> frappe._dict | None:
    """
    Get the Service Level Agreement that applies to `ticket`.

    A policy applies when its condition matches and it includes the ticket's
    priority. The default policy needs no condition but is still considered last.

    :param ticket: Ticket to use (document)
    :return: Applicable SLA, or None when no policy applies
    """
    QBSla = frappe.qb.DocType(DOCTYPE)
    QBPriority = frappe.qb.DocType("HD Service Level Priority")
    now = now_datetime()
    priority = ticket.priority
    q = (
        frappe.qb.from_(QBSla)
        .select(QBSla.name, QBSla.condition, QBSla.default_sla)
        .where(QBSla.enabled == True)
        .where(Criterion.any([QBSla.start_date.isnull(), QBSla.start_date <= now]))
        .where(Criterion.any([QBSla.end_date.isnull(), QBSla.end_date >= now]))
        .orderby(QBSla.default_sla)  # the Default SLA is considered last
        .orderby(QBSla.rank == 0)  # unranked sorts after ranked
        .orderby(QBSla.rank)
        .orderby(QBSla.creation)
    )
    if priority:
        q = (
            q.join(QBPriority, JoinType.inner)
            .on(QBPriority.parent == QBSla.name)
            .where(QBPriority.priority == priority)
        )
    context = None
    for sla in q.run(as_dict=True):
        if sla.default_sla:
            return sla
        if not sla.condition:
            continue  # a blank condition is not a false positive
        context = context or get_context(ticket)  # serialises the ticket, build once
        if frappe.safe_eval(sla.condition, None, context):
            return sla
    return None


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
