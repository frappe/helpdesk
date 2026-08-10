"""Per-ticket analytics: SLA timeline, response attribution metrics and
conversation summary. All durations are business seconds via the ticket's SLA
working hours; wall-clock fallback when the ticket has no SLA."""

import json
from typing import Callable

import frappe
from frappe import _
from frappe.utils import (
    cint,
    get_user_info_for_avatar,
    now_datetime,
    time_diff_in_seconds,
)

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
    "_assign",
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
    versions = version_changes(ticket)
    spans = pause_spans(versions)
    events, gaps = event_series(messages, details, working_seconds, spans)
    return {
        "has_sla": bool(details.sla),
        "timeline": build_timeline(details, working_seconds, messages, spans),
        "metrics": compute_metrics(gaps, details, working_seconds),
        "events": events,
        "summary": summary(ticket, messages, versions, details),
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


def event_series(
    messages: list[frappe._dict],
    details: frappe._dict,
    working_seconds: WorkingSeconds,
    spans: list[tuple],
) -> tuple[list[dict], dict[str, list[int]]]:
    """Conversation as timeline rail events plus the hand-off gap series per
    side. The description message and the first response are left out of events
    (they render as the created / first response milestones) but still feed the
    walk."""
    events = []
    gaps: dict[str, list[int]] = {"agent": [], "customer": []}
    names: dict[str, str] = {}
    previous = None
    first_sent_seen = False
    for index, message in enumerate(messages):
        wait = None
        if (
            previous
            and previous.sent_or_received == "Received"
            and message.sent_or_received == "Sent"
        ):
            # the SLA clock stops on hold, so paused time is not the agent's wait
            wait = max(
                0,
                (working_seconds(previous.creation, message.creation) or 0)
                - paused_overlap(
                    previous.creation, message.creation, spans, working_seconds
                ),
            )
            gaps["agent"].append(wait)
        elif (
            previous
            and previous.sent_or_received == "Sent"
            and message.sent_or_received == "Received"
        ):
            # customer gaps stay raw: replied tickets pause by design, so
            # subtracting pause time would zero the metric
            gaps["customer"].append(
                working_seconds(previous.creation, message.creation) or 0
            )
        is_first_response = (
            message.sent_or_received == "Sent"
            and not first_sent_seen
            and bool(details.first_responded_on)
        )
        if message.sent_or_received == "Sent":
            first_sent_seen = True
        if not is_description(index, message, details) and not is_first_response:
            if message.sender not in names:
                names[message.sender] = frappe.utils.get_fullname(message.sender)
            events.append(
                {
                    "side": (
                        "customer"
                        if message.sent_or_received == "Received"
                        else "agent"
                    ),
                    "at": message.creation,
                    "sender": message.sender,
                    "sender_name": names[message.sender],
                    "wait_seconds": wait,
                }
            )
        previous = message
    return events, gaps


def paused_overlap(
    start, end, spans: list[tuple], working_seconds: WorkingSeconds
) -> int:
    """Working seconds of (start, end) that fall inside pause spans."""
    total = 0
    for span_start, span_end in spans:
        clipped_start = max(start, span_start)
        clipped_end = min(end, span_end) if span_end else end
        if clipped_start < clipped_end:
            total += working_seconds(clipped_start, clipped_end) or 0
    return total


def is_description(index: int, message: frappe._dict, details: frappe._dict) -> bool:
    """The auto-created description Communication lands within seconds of the ticket."""
    return (
        index == 0
        and message.sent_or_received == "Received"
        and (elapsed(details.creation, message.creation) or 0) <= 60
    )


def compute_metrics(
    gaps: dict[str, list[int]], details: frappe._dict, working_seconds: WorkingSeconds
) -> dict:
    return {
        "avg_agent_gap": average(gaps["agent"]),
        "avg_customer_gap": average(gaps["customer"]),
        "hold_time": hold_seconds(details, working_seconds) or None,
    }


def hold_seconds(details: frappe._dict, working_seconds: WorkingSeconds) -> int:
    """Accumulated pause time, including the running pause on an active hold."""
    paused = cint(details.total_hold_time)
    if details.status_category == "Paused" and details.on_hold_since:
        paused += working_seconds(details.on_hold_since, now_datetime()) or 0
    return paused


def resolution_seconds(details: frappe._dict) -> int | None:
    if not details.resolution_date:
        return None
    # same fallback rule as useSLA.ts, see first_response_node
    return cint(details.resolution_time) or elapsed(
        details.creation, details.resolution_date
    )


def average(values: list) -> int | None:
    return round(sum(values) / len(values)) if values else None


def summary(
    ticket: str,
    messages: list[frappe._dict],
    versions: list[frappe._dict],
    details: frappe._dict,
) -> dict:
    customer = sum(1 for m in messages if m.sent_or_received == "Received")
    return {
        "customer_messages": customer,
        "agent_messages": len(messages) - customer,
        "internal_comments": frappe.db.count(
            "HD Ticket Comment", {"reference_ticket": ticket}
        ),
        "agents_involved": [
            get_user_info_for_avatar(user)
            for user in involved_agents(messages, details.get("_assign"))
        ],
        "churn": churn(versions),
    }


def involved_agents(messages: list[frappe._dict], assigned: str | None) -> list[str]:
    """Reply senders oldest first, then assignees who never replied."""
    senders = [m.sender for m in messages if m.sent_or_received == "Sent"]
    by_email = user_ids(senders)
    users = []
    for sender in senders:
        user = by_email.get(sender, sender)
        if user not in users:
            users.append(user)
    for user in frappe.parse_json(assigned or "[]"):
        if user not in users:
            users.append(user)
    return users


def user_ids(emails: list[str]) -> dict[str, str]:
    """Sender email -> User id, so a sender and an assignee that are the same
    person (admin@example.com / Administrator) collapse to one entry."""
    if not emails:
        return {}
    return dict(
        frappe.get_all(
            "User",
            filters={"email": ["in", list(set(emails))]},
            fields=["email", "name"],
            as_list=True,
            ignore_permissions=True,
        )
    )


def churn(versions: list[frappe._dict]) -> dict:
    """Routing churn from Version field diffs recorded by track_changes."""
    changed = [field for version in versions for field, old, new in version.changed]
    return {
        "sla_changes": changed.count("sla"),
        "team_changes": changed.count("agent_group"),
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


def pause_spans(versions: list[frappe._dict]) -> list[tuple]:
    """(start, end) status-paused windows from Version diffs, oldest first;
    end is None while the pause is still running."""
    paused_statuses = set(
        frappe.get_list(
            "HD Ticket Status",
            filters={"category": "Paused"},
            pluck="name",
            ignore_permissions=True,
        )
    )
    spans = []
    start = None
    for version in versions:
        for field, old, new in version.changed:
            if field != "status":
                continue
            if new in paused_statuses and old not in paused_statuses:
                start = start or version.creation
            elif old in paused_statuses and new not in paused_statuses and start:
                spans.append((start, version.creation))
                start = None
    if start:
        spans.append((start, None))
    return spans


def build_timeline(
    details: frappe._dict,
    working_seconds: WorkingSeconds,
    messages: list[frappe._dict],
    spans: list[tuple],
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
    # hold is a cumulative summary, not a point event; it sits before
    # resolution so the dashed leg reads "the clock to resolution stopped"
    if hold := hold_node(details, working_seconds, spans):
        nodes.append(hold)
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
        # mirrors useSLA.ts: the engine-recorded working-hours duration, else
        # wall clock from creation; sla_creation can postdate the response when
        # the SLA was re-applied, which would clamp the duration to 0
        took = cint(details.first_response_time) or elapsed(
            details.creation, details.first_responded_on
        )
        failed_by = cint(details.first_response_failed_by)
        if failed_by:
            node["eta"] = details.response_by
            return milestone(node, "breach", took, max(took - failed_by, 0), failed_by)
        if target is None:
            return {
                **node,
                "state": "done",
                "badge": badge(f"Responded in {fmt(took)}", "green"),
                "took": took,
                "target": None,
            }
        return milestone(node, "done", took, target)

    return pending_milestone(node, details.response_by, start, working_seconds)


def resolution_node(details: frappe._dict, working_seconds: WorkingSeconds) -> dict:
    start = details.service_level_agreement_creation or details.creation
    node = {"key": "resolution", "timestamp": details.resolution_date, "eta": None}

    if details.resolution_date:
        took = resolution_seconds(details)
        failed_by = cint(details.resolution_failed_by)
        if failed_by:
            node["eta"] = details.resolution_by
            return milestone(node, "breach", took, max(took - failed_by, 0), failed_by)
        spare = working_seconds(details.resolution_date, details.resolution_by)
        if spare is None:
            return {
                **node,
                "state": "done",
                "badge": badge(f"Resolved in {fmt(took)}", "green"),
                "took": took,
                "target": None,
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
    else:
        text, tone = badge_text or f"Fulfilled in {fmt(took)}", "green"
    return {
        **node,
        "state": state,
        "badge": badge(text, tone),
        "took": took,
        "target": target,
    }


def pending_milestone(
    node: dict, due_by, start, working_seconds: WorkingSeconds
) -> dict:
    if not due_by:
        return {**node, "state": "pending", "badge": None}
    now = now_datetime()
    target = working_seconds(start, due_by) or 0
    spent = working_seconds(start, now) or 0
    # countdowns are wall-clock on minute boundaries, exactly like the sidebar
    # SLA panel (useSLA coarseDuration); measurements (elapsed/target legs)
    # stay in working hours
    remaining = int(
        (
            due_by.replace(second=0, microsecond=0)
            - now.replace(second=0, microsecond=0)
        ).total_seconds()
    )
    if remaining < 0:
        return {
            **node,
            "state": "breach",
            "eta": due_by,
            "badge": badge(f"Overdue by {fmt(-remaining)}", "red"),
            "took": spent,
            "target": target,
        }
    return {
        **node,
        "state": "pending",
        "eta": due_by,
        "badge": badge(f"Due in {fmt(remaining)}", "gray"),
        "took": spent,
        "target": target,
    }


def hold_node(
    details: frappe._dict, working_seconds: WorkingSeconds, spans: list[tuple]
) -> dict | None:
    active = details.status_category == "Paused"
    paused = hold_seconds(details, working_seconds)
    if not paused and not active:
        return None
    window = pause_window(spans, active, details.on_hold_since)
    return {
        "key": "hold",
        "state": "hold",
        "active": active,
        "timestamp": details.on_hold_since if active else None,
        "window": window,
        "took": paused,
        "badge": badge(f"{fmt(paused)} paused", "amber"),
    }


def pause_window(spans: list[tuple], active: bool, on_hold_since) -> dict | None:
    """One aggregated span (first pause start to last resume).
    None when Versions were pruned; duration alone still renders."""
    start = spans[0][0] if spans else None
    end = spans[-1][1] if spans else None
    if active:
        start, end = start or on_hold_since, None
    if not start:
        return None
    return {"start": start, "end": end}


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
