"""OAuth2 provider templates for Helpdesk email accounts.

Each entry describes everything needed to build a Frappe ``Connected App`` for a
specific email provider so the user only has to supply ``client_id`` and
``client_secret`` from the frontend.

Keys per provider:
        - ``authorization_uri`` / ``token_uri``: OAuth2 endpoints used by Frappe's
          Connected App during the web application flow.
        - ``openid_configuration``: optional discovery URL (helpful for Google).
        - ``scopes``: scopes required for IMAP and SMTP access through OAuth.
        - ``query_params``: extra params appended to the authorization URL.
          Google needs ``access_type=offline`` and ``prompt=consent`` so a
          refresh token is actually returned on every consent.
        - ``email_account``: defaults applied to the ``Email Account`` doc when
          the OAuth flow is used (IMAP/SMTP servers, ports, SSL flags).
"""

GMAIL = "GMail"
OUTLOOK = "Outlook"

# One Connected App per provider per site. Using a fixed, URL-safe slug
# (no spaces, no per-email suffix) keeps the OAuth redirect URI stable so
# you only have to register it in Google Cloud Console / Azure Portal once
# and every mailbox under the same provider reuses it.
CONNECTED_APP_NAMES: dict[str, str] = {
    GMAIL: "helpdesk_gmail",
    OUTLOOK: "helpdesk_outlook",
}


def get_connected_app_name(service: str) -> str:
    return CONNECTED_APP_NAMES[service]


OAUTH_PROVIDERS: dict[str, dict] = {
    GMAIL: {
        "authorization_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "openid_configuration": "https://accounts.google.com/.well-known/openid-configuration",
        "scopes": ["https://mail.google.com/"],
        "query_params": {
            "access_type": "offline",
            "prompt": "consent",
        },
        "email_account": {
            "email_server": "imap.gmail.com",
            "use_imap": 1,
            "use_ssl": 1,
            "incoming_port": 993,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": 1,
        },
    },
    OUTLOOK: {
        "authorization_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_uri": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "openid_configuration": None,
        "scopes": [
            "https://outlook.office.com/IMAP.AccessAsUser.All",
            "https://outlook.office.com/SMTP.Send",
            "offline_access",
        ],
        "query_params": {
            "prompt": "consent",
        },
        "email_account": {
            "email_server": "outlook.office365.com",
            "use_imap": 1,
            "use_ssl": 1,
            "incoming_port": 993,
            "smtp_server": "smtp.office365.com",
            "smtp_port": 587,
            "use_tls": 1,
        },
    },
}


def is_supported(service: str) -> bool:
    return service in OAUTH_PROVIDERS


def get_provider(service: str) -> dict:
    return OAUTH_PROVIDERS[service]


def supported_services() -> list[str]:
    return list(OAUTH_PROVIDERS.keys())
