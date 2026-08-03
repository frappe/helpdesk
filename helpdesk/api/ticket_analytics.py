"""Per-ticket analytics: SLA timeline, response attribution metrics and
conversation summary. All durations are business seconds via the ticket's SLA
working hours; wall-clock fallback when the ticket has no SLA."""

import json
from typing import Callable

import frappe
from frappe import _
from frappe.utils import cint, formatdate, now_datetime, time_diff_in_seconds

from helpdesk.utils import agent_only

WorkingSeconds = Callable[[object, object], int | None]

TICKET_FIELDS = [
    "creation",
    "sla",
    "status",
    "status_category",
    "service_level_agreement_creation",
    "first_responded_on",
    "first_response_time",
    "first_response_failed_by",
    "response_by",
    "resolution_by",
    "resolution_date",
    "resolution_time",
    "resolution_failed_by",
    "on_hold_since",
    "total_hold_time",
]


@frappe.whitelist()
@agent_only
def get_ticket_analytics(ticket: str) -> dict:
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)
    details = frappe.db.get_value("HD Ticket", ticket, TICKET_FIELDS, as_dict=True)
    if not details:
        frappe.throw(_("Ticket {0} not found.").format(ticket))

    working_seconds = working_seconds_fn(details.sla)
    messages = conversation(ticket)
    agent_gaps = gap_series(messages, working_seconds)
    versions = version_changes(ticket)
    return {
        "has_sla": bool(details.sla),
        "timeline": build_timeline(details, working_seconds, messages, versions),
        "metrics": compute_metrics(agent_gaps, details, working_seconds),
        "gaps": agent_gaps,
        "first_response_target": first_response_target(details, working_seconds),
        "summary": summary(ticket, messages, versions),
    }


def working_seconds_fn(sla_name: str | None) -> WorkingSeconds:
    """(start, end) -> business seconds per the SLA calendar; wall-clock without an SLA."""
    if not sla_name:
        return elapsed
    sla = frappe.get_cached_doc("HD Service Level Agreement", sla_name)

    def working_seconds(start, end) -> int | None:
        if not start or not end:
            return None
        return max(0, cint(sla.calc_elapsed_time(start, end)))

    return working_seconds


def elapsed(start, end) -> int | None:
    if not start or not end:
        return None
    return max(0, cint(time_diff_in_seconds(end, start)))


def conversation(ticket: str) -> list[frappe._dict]:
    # ticket read is verified above; sub-reads are scoped to it
    return frappe.get_list(
        "Communication",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_name": ticket,
            "communication_type": "Communication",
        },
        fields=["sent_or_received", "sender", "creation"],
        order_by="creation asc",
        ignore_permissions=True,
    )


def gap_series(
    messages: list[frappe._dict], working_seconds: WorkingSeconds
) -> list[dict]:
    """Direction-flip walk: each Received->Sent flip is an agent response gap."""
    agent_gaps = []
    previous = None
    for message in messages:
        if (
            previous
            and previous.sent_or_received == "Received"
            and message.sent_or_received == "Sent"
        ):
            agent_gaps.append(
                {
                    "replied_at": message.creation,
                    "agent": message.sender,
                    "gap_seconds": working_seconds(previous.creation, message.creation)
                    or 0,
                }
            )
        previous = message
    return agent_gaps


def compute_metrics(
    agent_gaps: list[dict], details: frappe._dict, working_seconds: WorkingSeconds
) -> dict:
    gaps = [row["gap_seconds"] for row in agent_gaps]
    return {
        "avg_agent_gap": average(gaps),
        "resolution_time": resolution_seconds(details, working_seconds),
        "longest_agent_silence": max(gaps) if gaps else None,
    }


def resolution_seconds(
    details: frappe._dict, working_seconds: WorkingSeconds
) -> int | None:
    if not details.resolution_date:
        return None
    start = details.service_level_agreement_creation or details.creation
    return cint(details.resolution_time) or working_seconds(
        start, details.resolution_date
    )


def average(values: list) -> int | None:
    return round(sum(values) / len(values)) if values else None


def first_response_target(
    details: frappe._dict, working_seconds: WorkingSeconds
) -> int | None:
    start = details.service_level_agreement_creation or details.creation
    return working_seconds(start, details.response_by)


def summary(
    ticket: str, messages: list[frappe._dict], versions: list[frappe._dict]
) -> dict:
    customer = sum(1 for m in messages if m.sent_or_received == "Received")
    agents = []
    for m in messages:
        if m.sent_or_received == "Sent" and m.sender not in agents:
            agents.append(m.sender)
    return {
        "customer_messages": customer,
        "agent_messages": len(messages) - customer,
        "total_exchanges": len(messages),
        "internal_comments": frappe.db.count(
            "HD Ticket Comment", {"reference_ticket": ticket}
        ),
        "agents_involved": [
            {"user": user, "full_name": frappe.utils.get_fullname(user)}
            for user in agents
        ],
        "churn": churn(ticket, versions),
    }


def churn(ticket: str, versions: list[frappe._dict]) -> dict:
    """Routing churn from Version diffs and assignment history. Reassignments follow the
    assignee-stations model (distinct assignees - 1), so simultaneous multi-assignee
    tickets inflate the count slightly; acceptable for v1."""
    changed = [field for version in versions for field, old, new in version.changed]
    assignees = {
        row.allocated_to
        for row in frappe.get_list(
            "ToDo",
            filters={"reference_type": "HD Ticket", "reference_name": ticket},
            fields=["allocated_to"],
            ignore_permissions=True,
        )
        if row.allocated_to
    }
    return {
        "sla_changes": changed.count("sla"),
        "team_changes": changed.count("agent_group"),
        "reassignments": max(0, len(assignees) - 1),
    }


def version_changes(ticket: str) -> list[frappe._dict]:
    """Field diffs recorded by track_changes, oldest first: [{creation, changed: [(field, old, new)]}]."""
    rows = frappe.get_list(
        "Version",
        filters={"ref_doctype": "HD Ticket", "docname": ticket},
        fields=["creation", "data"],
        order_by="creation asc",
        ignore_permissions=True,
    )
    versions = []
    for row in rows:
        try:
            changed = json.loads(row.data).get("changed") or []
        except (ValueError, TypeError):
            continue
        versions.append(
            frappe._dict(creation=row.creation, changed=[tuple(c) for c in changed])
        )
    return versions


def build_timeline(
    details: frappe._dict,
    working_seconds: WorkingSeconds,
    messages: list[frappe._dict],
    versions: list[frappe._dict],
) -> list[dict]:
    nodes = [
        {
            "key": "created",
            "state": "done",
            "timestamp": details.creation,
            "badge": None,
        },
        first_response_node(details, working_seconds),
    ]
    if hold := hold_node(details, working_seconds, versions):
        nodes.append(hold)
    if exchanges := exchanges_node(messages):
        nodes.append(exchanges)
    nodes.append(resolution_node(details, working_seconds))
    return nodes


def first_response_node(details: frappe._dict, working_seconds: WorkingSeconds) -> dict:
    start = details.service_level_agreement_creation or details.creation
    target = working_seconds(start, details.response_by)
    node = {
        "key": "first_response",
        "timestamp": details.first_responded_on,
        "eta": None,
    }

    if details.first_responded_on:
        took = cint(details.first_response_time) or working_seconds(
            start, details.first_responded_on
        )
        failed_by = cint(details.first_response_failed_by)
        if failed_by:
            return milestone(node, "breach", took, max(took - failed_by, 0), failed_by)
        if target is None:
            return {
                **node,
                "state": "done",
                "badge": badge(f"Responded in {fmt(took)}", "green"),
                "took": took,
                "target": None,
                "leg_label": f"took {fmt(took)}",
            }
        return milestone(node, "done", took, target)

    return pending_milestone(node, details.response_by, start, working_seconds)


def resolution_node(details: frappe._dict, working_seconds: WorkingSeconds) -> dict:
    start = details.service_level_agreement_creation or details.creation
    node = {"key": "resolution", "timestamp": details.resolution_date, "eta": None}

    if details.resolution_date:
        took = resolution_seconds(details, working_seconds)
        failed_by = cint(details.resolution_failed_by)
        if failed_by:
            return milestone(node, "breach", took, max(took - failed_by, 0), failed_by)
        spare = working_seconds(details.resolution_date, details.resolution_by)
        if spare is None:
            return {
                **node,
                "state": "done",
                "badge": badge(f"Resolved in {fmt(took)}", "green"),
                "took": took,
                "target": None,
                "leg_label": f"took {fmt(took)}",
            }
        return milestone(
            node, "done", took, took + spare, badge_text=f"{fmt(spare)} to spare"
        )

    # Resolved category without a resolution_date means auto-closed
    if details.status_category == "Resolved":
        return {
            **node,
            "state": "done",
            "badge": badge("Closed without resolution", "gray"),
        }

    return pending_milestone(node, details.resolution_by, start, working_seconds)


def milestone(
    node: dict,
    state: str,
    took: int,
    target: int,
    failed_by: int = 0,
    badge_text: str | None = None,
) -> dict:
    if state == "breach":
        text, tone = f"Failed by {fmt(failed_by)}", "red"
        progress = target / (target + failed_by) if target + failed_by else 0
    else:
        text, tone = badge_text or f"Within SLA · {fmt(target)} target", "green"
        progress = None
    return {
        **node,
        "state": state,
        "badge": badge(text, tone),
        "took": took,
        "target": target,
        "leg_label": f"took {fmt(took)} · {fmt(target)} target",
        "progress": progress,
    }


def pending_milestone(
    node: dict, due_by, start, working_seconds: WorkingSeconds
) -> dict:
    if not due_by:
        return {**node, "state": "pending", "badge": None}
    now = now_datetime()
    target = working_seconds(start, due_by) or 0
    spent = working_seconds(start, now) or 0
    if spent > target:
        overdue = spent - target
        return {
            **node,
            "state": "breach",
            "eta": due_by,
            "badge": badge(f"Overdue by {fmt(overdue)}", "red"),
            "took": spent,
            "target": target,
            "leg_label": f"{fmt(spent)} elapsed · {fmt(target)} target",
            "progress": target / spent if spent else 0,
        }
    return {
        **node,
        "state": "pending",
        "eta": due_by,
        "badge": None,
        "took": spent,
        "target": target,
        "leg_label": f"{fmt(spent)} elapsed · {fmt(target)} target",
        "progress": min(spent / target, 1) if target else 0,
    }


def hold_node(
    details: frappe._dict, working_seconds: WorkingSeconds, versions: list[frappe._dict]
) -> dict | None:
    active = details.status_category == "Paused"
    paused = cint(details.total_hold_time)
    if active and details.on_hold_since:
        paused += working_seconds(details.on_hold_since, now_datetime()) or 0
    if not paused and not active:
        return None
    window = pause_window(versions, active, details.on_hold_since)
    return {
        "key": "hold",
        "state": "hold",
        "active": active,
        "timestamp": details.on_hold_since if active else None,
        "window": window,
        "took": paused,
        "badge": badge(f"{fmt(paused)} paused", "amber"),
    }


def pause_window(
    versions: list[frappe._dict], active: bool, on_hold_since
) -> dict | None:
    """One aggregated span (first pause start to last resume) from Version status diffs.
    None when Versions were pruned; duration alone still renders."""
    paused_statuses = set(
        frappe.get_list(
            "HD Ticket Status",
            filters={"category": "Paused"},
            pluck="name",
            ignore_permissions=True,
        )
    )
    start = end = None
    for version in versions:
        for field, old, new in version.changed:
            if field != "status":
                continue
            if new in paused_statuses and old not in paused_statuses:
                start = start or version.creation
            elif old in paused_statuses and new not in paused_statuses:
                end = version.creation
    if active:
        start, end = start or on_hold_since, None
    if not start:
        return None
    return {"start": start, "end": end}


def exchanges_node(messages: list[frappe._dict]) -> dict | None:
    if len(messages) < 2:
        return None
    first = formatdate(messages[0].creation, "MMM d")
    last = formatdate(messages[-1].creation, "MMM d")
    return {
        "key": "exchanges",
        "state": "done",
        "count": len(messages),
        "timestamp": None,
        "range": first if first == last else f"{first} – {last}",
    }


def badge(text: str, tone: str) -> dict:
    return {"text": text, "tone": tone}


def fmt(seconds: int | None) -> str:
    """Duration as at most two units, never decimals: '20h 25m', '3d 2h', '45s'."""
    seconds = cint(seconds)
    minutes, days = (seconds // 60) % 60, seconds // 86400
    hours = (seconds // 3600) % 24
    if days:
        return f"{days}d {hours}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return f"{seconds}s"
