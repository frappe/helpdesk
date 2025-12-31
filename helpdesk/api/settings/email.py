import frappe


@frappe.whitelist()
def create_email_account(data):
    frappe.has_permission("Email Account", "create", throw=True)

    service = data.get("service")
    service_config = email_service_config.get(service)
    if not service_config and service != "Custom":
        return "Service not supported"

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
