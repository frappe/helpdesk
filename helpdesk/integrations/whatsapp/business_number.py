import re

import frappe
from frappe.model.document import Document

CACHE_KEY = "helpdesk:whatsapp_business_number:{0}"
CACHE_SECONDS = 24 * 60 * 60
# a failed lookup is retried sooner, so an outage doesn't hide the link for a day
FAILURE_CACHE_SECONDS = 10 * 60
TIMEOUT_SECONDS = 3


def get_business_number(last_incoming: dict | None) -> str | None:
    """Digits of the Business Number a ticket's customer last wrote to (get_last_incoming), for a wa.me link."""
    account = get_ticket_account(last_incoming)
    if not account:
        return None
    doc = frappe.get_cached_doc("WA Account", account)
    # modified in the key, so editing the account drops a stale or failed lookup
    key = CACHE_KEY.format(f"{account}:{doc.modified}")
    number = frappe.cache.get_value(key)
    if number is None:
        number = fetch_display_number(doc)
        expiry = CACHE_SECONDS if number else FAILURE_CACHE_SECONDS
        frappe.cache.set_value(key, number, expires_in_sec=expiry)
    return number or None


def get_ticket_account(last_incoming: dict | None) -> str | None:
    if last_incoming and last_incoming.whatsapp_account:
        return last_incoming.whatsapp_account
    return frappe.db.get_single_value("WA Settings", "default_account")


def fetch_display_number(account: Document) -> str:
    """Ask Meta for the account's display number, which the whatsapp app doesn't store; empty on failure."""
    from whatsapp.whatsapp.doctype.wa_message.wa_message import _get_whatsapp_client

    if not (account.phone_id and account.get_password("access_token", False)):
        return ""
    client = _get_whatsapp_client(account, frappe.get_cached_doc("WA Settings"))
    try:
        response = client._request(
            "GET",
            account.phone_id,
            params={"fields": "display_phone_number"},
            timeout=TIMEOUT_SECONDS,
        )
        return re.sub(r"\D", "", str(response.get("display_phone_number") or ""))
    except Exception:
        return ""
