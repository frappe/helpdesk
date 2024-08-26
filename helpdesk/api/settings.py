import frappe


@frappe.whitelist()
def create_email_account(
    service, email_account_name, email_id, password="", api_key="", api_secret=""
):
    service_config = email_service_config.get(service)
    if not service_config:
        return "Service not supported"

    try:
        email_doc = frappe.get_doc(
            {
                "doctype": "Email Account",
                "email_id": email_id,
                "email_account_name": email_account_name,
                "service": service,
                "enable_incoming": 1,
                "enable_outgoing": 1,
                "default_incoming": 1,
                "default_outgoing": 1,
                "email_sync_option": "ALL",
                "initial_sync_count": 100,
                "create_contact": 1,
                "track_email_status": 1,
                "use_tls": 1,
                "use_imap": 1,
                "smtp_port": 587,
                **service_config,
            }
        )
        email_doc.append(
            "imap_folder", {"append_to": "HD Ticket", "folder_name": "INBOX"}
        )
        if service == "Frappemail":
            email_doc.api_key = api_key
            email_doc.api_secret = api_secret
        else:
            email_doc.password = password

        email_doc.save()
        return "Email Account Created Successfully"
    except Exception as e:
        frappe.throw(str(e))


email_service_config = {
    "FrappeMail": {
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
    "Yandex": {
        "email_server": "imap.yandex.com",
        "use_ssl": 1,
        "smtp_server": "smtp.yandex.com",
        "smtp_port": 587,
    },
}
