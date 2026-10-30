import frappe, requests
from frappe.utils import add_to_date, now_datetime

URL = "https://api.zenhub.com/public/graphql"
MAX_RETRIES = 5
RETRY_AFTER_MINUTES = 15


def _gql(query, variables=None):
    h = {"Authorization": f"Bearer {frappe.conf.zenhub_token}"}
    r = requests.post(URL, json={"query": query, "variables": variables or {}},
                      headers=h, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise Exception(data["errors"])
    return data["data"]


def queue_ticket(ticket_name):
    """Queue a ZenHub issue for this ticket, once."""
    if not frappe.conf.get("zenhub_repository_id"):
        return
    row = frappe.db.get_value("HD Ticket", ticket_name,
                              ["zenhub_issue_id", "zenhub_sync_status"], as_dict=True)
    if not row or row.zenhub_issue_id or row.zenhub_sync_status == "Queued":
        return
    frappe.db.set_value("HD Ticket", ticket_name,
                        {"zenhub_sync_status": "Queued", "zenhub_last_attempt": now_datetime()},
                        update_modified=False)
    frappe.enqueue("helpdesk.integrations.zenhub.sync_ticket",
                   ticket_name=ticket_name, queue="short", enqueue_after_commit=True)


def sync_ticket(ticket_name):
    doc = frappe.get_doc("HD Ticket", ticket_name)
    if doc.zenhub_issue_id:
        return
    try:
        title = (frappe.conf.get("zenhub_title_prefix") or "") + (doc.subject or ticket_name)
        link = f"{frappe.utils.get_url()}/helpdesk/tickets/{doc.name}"
        desc = frappe.utils.strip_html(doc.description or "")[:1500]
        body = f"Raised from Helpdesk ticket {doc.name}\n{link}\n\n{desc}"
        data = _gql("""mutation($input: CreateIssueInput!){
            createIssue(input:$input){ issue { id number } } }""",
            {"input": {"repositoryId": frappe.conf.zenhub_repository_id,
                       "title": title, "body": body}})
        issue = data["createIssue"]["issue"]
        frappe.db.set_value("HD Ticket", ticket_name, {
            "zenhub_issue_id": issue["id"],
            "zenhub_issue_number": issue["number"],
            "zenhub_sync_status": "Synced"}, update_modified=False)
    except Exception:
        tries = (doc.zenhub_retry_count or 0) + 1
        frappe.db.set_value("HD Ticket", ticket_name, {
            "zenhub_sync_status": "Failed",
            "zenhub_retry_count": tries,
            "zenhub_last_attempt": now_datetime()}, update_modified=False)
        frappe.log_error(title=f"ZenHub sync failed ({tries}/{MAX_RETRIES}): {ticket_name}")


def retry_failed():
    """Scheduled: re-send failed or stuck tickets, at most MAX_RETRIES times."""
    if not frappe.conf.get("zenhub_repository_id"):
        return
    cutoff = add_to_date(now_datetime(), minutes=-RETRY_AFTER_MINUTES)
    failed = frappe.get_all("HD Ticket", filters={
        "zenhub_sync_status": "Failed", "zenhub_retry_count": ["<", MAX_RETRIES],
        "zenhub_last_attempt": ["<", cutoff]}, pluck="name", limit=20)
    stuck = frappe.get_all("HD Ticket", filters={
        "zenhub_sync_status": "Queued", "zenhub_last_attempt": ["<", cutoff]},
        pluck="name", limit=20)
    for name in failed + stuck:
        frappe.db.set_value("HD Ticket", name, "zenhub_last_attempt", now_datetime(),
                            update_modified=False)   # stops the next run grabbing it again
        frappe.enqueue("helpdesk.integrations.zenhub.sync_ticket",
                       ticket_name=name, queue="short")