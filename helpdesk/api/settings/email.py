from typing import Any
from urllib.parse import quote

import frappe
from frappe import _

from helpdesk.api.settings.oauth_providers import (
    get_connected_app_name,
    get_provider,
    is_supported,
    supported_services,
)


@frappe.whitelist()
def create_email_account(data: dict[str, Any]):
    frappe.has_permission("Email Account", "create", throw=True)

    service: str = data.get("service", "")
    service_config = email_service_config.get(service)
    if not service_config and service != "Custom":
        return frappe.throw(_("Service not supported"))

    try:
        email_doc = frappe.get_doc(
            {
                "doctype": "Email Account",
                "email_id": data.get("email_id"),
                "email_account_name": data.get("email_account_name"),
                "service": service,
                "enable_incoming": data.get("enable_incoming"),
                "enable_outgoing": data.get("enable_outgoing"),
                "default_incoming": data.get("default_incoming"),
                "default_outgoing": data.get("default_outgoing"),
                "email_sync_option": "ALL",
                "initial_sync_count": 100,
                "create_contact": 1,
                "track_email_status": 1,
                "use_tls": 1,
                "use_imap": 1,
                "smtp_port": 587,
                **(service_config or {}),
            }
        )
        if service == "Frappe Mail":
            email_doc.api_key = data.get("api_key")
            email_doc.api_secret = data.get("api_secret")
            email_doc.frappe_mail_site = data.get("frappe_mail_site")
            email_doc.append_to = "HD Ticket"
        else:
            if service == "Custom":
                email_doc.service = ""
                email_doc.domain = data.get("domain")
                email_doc.email_server = data.get("email_server")
                email_doc.incoming_port = data.get("incoming_port")
                email_doc.smtp_server = data.get("smtp_server")
                email_doc.smtp_port = data.get("smtp_port") or 587
                email_doc.use_ssl = data.get("use_ssl") or 0
                email_doc.use_starttls = data.get("use_starttls") or 0
                email_doc.use_tls = data.get("use_tls") or 0
                email_doc.use_ssl_for_outgoing = data.get("use_ssl_for_outgoing") or 0
                email_doc.validate_ssl_certificate = data.get(
                    "validate_ssl_certificate", 1
                )
                email_doc.validate_ssl_certificate_for_outgoing = data.get(
                    "validate_ssl_certificate_for_outgoing", 1
                )
            email_doc.append(
                "imap_folder", {"append_to": "HD Ticket", "folder_name": "INBOX"}
            )
            email_doc.password = data.get("password")
            # validate whether the credentials are correct
            email_doc.get_incoming_server()

        # if correct credentials, save the email account
        email_doc.save()
        return email_doc.name
    except Exception as e:
        frappe.throw(str(e))


email_service_config = {
    "Frappe Mail": {
        "domain": None,
        "password": None,
        "awaiting_password": 0,
        "ascii_encode_password": 0,
        "login_id_is_different": 0,
        "login_id": None,
        "use_imap": 0,
        "use_ssl": 0,
        "validate_ssl_certificate": 0,
        "use_starttls": 0,
        "email_server": None,
        "incoming_port": 0,
        "always_use_account_email_id_as_sender": 1,
        "use_tls": 0,
        "use_ssl_for_outgoing": 0,
        "smtp_server": None,
        "smtp_port": None,
        "no_smtp_authentication": 0,
    },
    "GMail": {
        "email_server": "imap.gmail.com",
        "use_ssl": 1,
        "smtp_server": "smtp.gmail.com",
    },
    "Outlook": {
        "email_server": "imap-mail.outlook.com",
        "use_ssl": 1,
        "smtp_server": "smtp-mail.outlook.com",
    },
    # Alias for service values already stored by Desk/Email Account in older installs
    # (e.g. Outlook.com) to preserve backwards compatibility without migrations.
    "Outlook.com": {
        "email_server": "imap-mail.outlook.com",
        "use_ssl": 1,
        "smtp_server": "smtp-mail.outlook.com",
    },
    "Sendgrid": {
        "smtp_server": "smtp.sendgrid.net",
        "smtp_port": 587,
    },
    "SparkPost": {
        "smtp_server": "smtp.sparkpostmail.com",
    },
    "Yahoo": {
        "email_server": "imap.mail.yahoo.com",
        "use_ssl": 1,
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
    },
    # Alias for service values already stored by Desk/Email Account in older installs
    # (e.g. Yahoo Mail) to preserve backwards compatibility without migrations.
    "Yahoo Mail": {
        "email_server": "imap.mail.yahoo.com",
        "use_ssl": 1,
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
    },
    "Yandex": {
        "email_server": "imap.yandex.com",
        "use_ssl": 1,
        "smtp_server": "smtp.yandex.com",
        "smtp_port": 587,
    },
    # Alias for service values already stored by Desk/Email Account in older installs
    # (e.g. Yandex.Mail) to preserve backwards compatibility without migrations.
    "Yandex.Mail": {
        "email_server": "imap.yandex.com",
        "use_ssl": 1,
        "smtp_server": "smtp.yandex.com",
        "smtp_port": 587,
    },
    "Custom": {},
}


# -----------------------------------------------------------------------------
# OAuth (Gmail / Outlook)
# -----------------------------------------------------------------------------


@frappe.whitelist()
def get_oauth_redirect_uri(service: str) -> dict[str, str]:
    """Return the exact redirect URI to register in Google Cloud Console /
    Azure Portal for this provider.

    This is computed from the site URL and the deterministic Connected App
    name (``helpdesk_gmail`` / ``helpdesk_outlook``) — it does not depend on
    the Connected App existing yet, so the frontend can show it on the
    first-time setup screen before the user clicks Connect.
    """

    if not is_supported(service):
        frappe.throw(
            _("OAuth is not supported for {0}. Supported providers: {1}").format(
                service or _("this service"), ", ".join(supported_services())
            )
        )

    name = get_connected_app_name(service)
    base = frappe.utils.get_url()
    redirect_uri = (
        f"{base}/api/method/frappe.integrations.doctype.connected_app"
        f".connected_app.callback/{name}"
    )

    return {
        "redirect_uri": redirect_uri,
        "connected_app": name,
        "site_url": base,
    }


@frappe.whitelist()
def initiate_oauth_email(data: dict[str, Any]):
    """Create (or reuse) a Connected App, wire up an Email Account in OAuth
    mode, and return an authorization URL the frontend should redirect to.

    Only ``client_id``, ``client_secret``, ``service`` and ``email_id`` are
    required from the user — everything else (authorization URL, token URL,
    scopes, redirect URI, IMAP/SMTP servers) is filled in from the provider
    template defined in ``oauth_providers.py``.
    """

    frappe.has_permission("Email Account", "create", throw=True)
    frappe.has_permission("Connected App", "create", throw=True)

    service = (data or {}).get("service", "")
    if not is_supported(service):
        frappe.throw(
            _("OAuth is not supported for {0}. Supported providers: {1}").format(
                service or _("this service"), ", ".join(supported_services())
            )
        )

    client_id = (data.get("client_id") or "").strip()
    client_secret = (data.get("client_secret") or "").strip()
    email_id = (data.get("email_id") or "").strip()
    email_account_name = (data.get("email_account_name") or "").strip()

    if not client_id:
        frappe.throw(_("Client ID is required"))
    if not client_secret:
        frappe.throw(_("Client Secret is required"))
    if not email_id:
        frappe.throw(_("Email ID is required"))
    if not email_account_name:
        frappe.throw(_("Account name is required"))

    connected_app = _upsert_connected_app(service, client_id, client_secret)
    email_account = _upsert_oauth_email_account(
        service=service,
        data=data,
        connected_app=connected_app.name,
    )

    success_uri = _build_success_uri(email_account.name)
    redirect_url = connected_app.initiate_web_application_flow(
        user=frappe.session.user, success_uri=success_uri
    )

    return {
        "redirect_url": redirect_url,
        "email_account": email_account.name,
        "connected_app": connected_app.name,
    }


@frappe.whitelist()
def get_oauth_status(email_account: str) -> dict[str, Any]:
    """Return whether the given Email Account has a usable OAuth token.

    Used by the frontend to decide between a "Connected" badge and a
    "Reconnect" CTA on accounts that authenticate via OAuth.
    """

    frappe.has_permission("Email Account", "read", throw=True)

    if not frappe.db.exists("Email Account", email_account):
        frappe.throw(_("Email Account {0} not found").format(email_account))

    doc = frappe.get_doc("Email Account", email_account)

    if doc.auth_method != "OAuth" or not doc.connected_app:
        return {"is_oauth": False, "connected": False}

    from frappe.integrations.doctype.connected_app.connected_app import has_token

    connected_user = doc.connected_user or frappe.session.user
    connected = bool(has_token(doc.connected_app, connected_user))

    return {
        "is_oauth": True,
        "connected": connected,
        "connected_app": doc.connected_app,
        "connected_user": connected_user,
    }


@frappe.whitelist()
def reconnect_oauth_email(email_account: str) -> dict[str, Any]:
    """Restart the OAuth flow for an existing Email Account without requiring
    the user to re-enter the client_id / client_secret.
    """

    frappe.has_permission("Email Account", "write", throw=True)

    doc = frappe.get_doc("Email Account", email_account)
    if doc.auth_method != "OAuth" or not doc.connected_app:
        frappe.throw(
            _("Email Account {0} is not configured for OAuth").format(email_account)
        )

    connected_app = frappe.get_doc("Connected App", doc.connected_app)
    doc.connected_user = frappe.session.user
    doc.save(ignore_permissions=False)

    success_uri = _build_success_uri(doc.name)
    redirect_url = connected_app.initiate_web_application_flow(
        user=frappe.session.user, success_uri=success_uri
    )

    return {"redirect_url": redirect_url, "email_account": doc.name}


def _upsert_connected_app(service: str, client_id: str, client_secret: str):
    """Create or update the single Helpdesk Connected App for this provider.

    One Connected App per provider per site (e.g. ``helpdesk_gmail``) so the
    redirect URI is stable and only has to be registered once in the
    provider's developer console. Every mailbox using the same provider on
    this site shares these client credentials. The Connected App's
    ``validate()`` auto-fills the ``redirect_uri`` from the site URL — we
    never set it by hand.
    """

    provider = get_provider(service)
    name = get_connected_app_name(service)

    is_new = not frappe.db.exists("Connected App", name)
    if is_new:
        doc = frappe.new_doc("Connected App")
        doc.provider_name = name
    else:
        doc = frappe.get_doc("Connected App", name)

    doc.client_id = client_id
    doc.client_secret = client_secret
    doc.authorization_uri = provider["authorization_uri"]
    doc.token_uri = provider["token_uri"]
    doc.openid_configuration = provider.get("openid_configuration")

    _sync_child_table(doc, "scopes", "scope", provider["scopes"])
    _sync_query_params(doc, provider.get("query_params") or {})

    if is_new:
        doc.insert(set_name=name, ignore_permissions=False)
    else:
        doc.save(ignore_permissions=False)

    return doc


def _upsert_oauth_email_account(service: str, data: dict[str, Any], connected_app: str):
    """Create the Email Account in OAuth mode (or update an existing one).

    IMAP/SMTP server fields are taken from the provider template so the user
    never has to enter them. The doc is *not* validated against a live
    connection yet — that happens on first incoming/outgoing send, by which
    point the OAuth callback will have populated the Token Cache.
    """

    provider = get_provider(service)
    defaults = provider["email_account"]
    email_account_name = data["email_account_name"]
    email_id = data["email_id"]

    if frappe.db.exists("Email Account", {"email_account_name": email_account_name}):
        doc = frappe.get_doc(
            "Email Account", {"email_account_name": email_account_name}
        )
    else:
        doc = frappe.new_doc("Email Account")
        doc.email_account_name = email_account_name
        doc.append("imap_folder", {"append_to": "HD Ticket", "folder_name": "INBOX"})

    doc.email_id = email_id
    doc.service = service
    doc.auth_method = "OAuth"
    doc.connected_app = connected_app
    doc.connected_user = frappe.session.user
    doc.awaiting_password = 0
    doc.password = None

    doc.enable_incoming = 1 if data.get("enable_incoming") else 0
    doc.enable_outgoing = 1 if data.get("enable_outgoing") else 0
    doc.default_incoming = 1 if data.get("default_incoming") else 0
    doc.default_outgoing = 1 if data.get("default_outgoing") else 0

    doc.email_sync_option = doc.email_sync_option or "ALL"
    doc.initial_sync_count = doc.initial_sync_count or 100
    doc.create_contact = 1
    doc.track_email_status = 1

    for field, value in defaults.items():
        doc.set(field, value)

    doc.save(ignore_permissions=False)
    return doc


def _sync_child_table(
    doc, table_field: str, value_field: str, values: list[str]
) -> None:
    """Make ``doc.<table_field>`` match ``values`` exactly, comparing by ``value_field``."""

    existing = {row.get(value_field) for row in (doc.get(table_field) or [])}
    desired = set(values)
    if existing == desired:
        return

    doc.set(table_field, [])
    for value in values:
        doc.append(table_field, {value_field: value})


def _sync_query_params(doc, params: dict[str, str]) -> None:
    existing = {row.key: row.value for row in (doc.get("query_parameters") or [])}
    if existing == params:
        return

    doc.set("query_parameters", [])
    for key, value in params.items():
        doc.append("query_parameters", {"key": key, "value": value})


def _build_success_uri(email_account: str) -> str:
    """URL the user lands on after Frappe finishes the OAuth callback.

    Sends them back to the Helpdesk SPA with a marker so the frontend can
    show a "Connected" toast and refresh the email account list.
    """

    base = frappe.utils.get_url()
    return f"{base}/helpdesk?oauth_connected={quote(email_account)}"
