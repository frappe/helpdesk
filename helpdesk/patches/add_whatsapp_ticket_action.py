import frappe

from helpdesk.integrations.whatsapp.account import add_ticket_action
from helpdesk.integrations.whatsapp.setup import is_whatsapp_installed


def execute() -> None:
    """Every account made tickets before Create tickets existed, so keep it that way."""
    if not is_whatsapp_installed():
        return
    for account in frappe.get_all("WA Account", pluck="name"):
        add_ticket_action(account)
