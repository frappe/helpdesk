import frappe

TICKET_DOCTYPE = "HD Ticket"
TICKET_ACTION = {"append_to": TICKET_DOCTYPE, "trigger_on": "Incoming"}


def creates_tickets(account: str | None) -> bool:
    """Whether the account's incoming messages become tickets: it has an HD Ticket append action."""
    return bool(
        account
        and frappe.db.exists(
            "WA Account Append",
            {
                "parent": account,
                "parenttype": "WA Account",
                "append_to": TICKET_DOCTYPE,
            },
        )
    )


def add_ticket_action(account: str) -> None:
    """Make an account's incoming messages tickets, unless it already does."""
    if creates_tickets(account):
        return
    doc = frappe.get_doc("WA Account", account)
    doc.append("append_actions", TICKET_ACTION)
    doc.save(ignore_permissions=True)


def default_ticket_action(doc, method=None) -> None:
    """WA Account before_insert: an account added with Connect with Meta creates tickets, like one
    added by hand."""
    if doc.get("connected_with_meta") and not any(
        row.append_to == TICKET_DOCTYPE for row in doc.append_actions
    ):
        doc.append("append_actions", TICKET_ACTION)
