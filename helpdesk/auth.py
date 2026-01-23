import json

import frappe

ALLOWED_PATHS = [
    "/api/method/ping",
    "/api/method/login",
    "/api/method/logout",
    "/api/method/frappe.core.doctype.communication.email.mark_email_as_seen",
    "/api/method/frappe.realtime.get_user_info",
    "/api/method/frappe.realtime.can_subscribe_doc",
    "/api/method/frappe.realtime.can_subscribe_doctype",
    "/api/method/frappe.realtime.has_permission",
    "/api/method/frappe.integrations.oauth2.authorize",
    "/api/method/frappe.integrations.oauth2.approve",
    "/api/method/frappe.integrations.oauth2.get_token",
    "/api/method/frappe.www.login.login_via_google",
    "/api/method/frappe.www.login.login_via_github",
    "/api/method/frappe.www.login.login_via_facebook",
    "/api/method/frappe.www.login.login_via_frappe",
    "/api/method/frappe.www.login.login_via_office365",
    "/api/method/frappe.www.login.login_via_salesforce",
    "/api/method/frappe.integrations.oauth2_logins.custom",
    "/api/method/frappe.www.login.login_via_fairlogin",
    "/api/method/frappe.www.login.login_via_keycloak",
    "/api/method/frappe.www.login.custom",
    "api/method/frappe.core.api.user_invitation.get_pending_invitations",
    "/api/method/frappe.integrations.oauth2.openid_profile",
    "/api/method/frappe.website.doctype.web_page_view.web_page_view.make_view_log",
    "/api/method/upload_file",
    "/api/method/frappe.search.web_search",
    "/api/method/frappe.email.queue.unsubscribe",
    "/api/method/frappe.website.doctype.web_form.web_form.accept",
    "/api/method/frappe.core.doctype.user.user.test_password_strength",
    "/api/method/frappe.core.doctype.user.user.update_password",
    "/api/method/frappe.utils.telemetry.pulse.client.is_enabled",
    "/api/method/frappe.client.get_value",
    "/api/method/frappe.client.get_count",
    "/api/method/frappe.client.get",
    "/api/method/frappe.client.insert",
    "/api/method/frappe.client.set_value",
    "/api/method/frappe.client.delete",
    "/api/method/frappe.client.get_list",
    "/api/method/frappe.client.rename_doc",
    "/api/method/frappe.onboarding.get_onboarding_status",
    "/api/method/frappe.utils.print_format.download_pdf",
    "/api/method/frappe.desk.search.search_link",
    "/api/method/frappe.core.doctype.communication.email.make",
    "/api/method/frappe.core.doctype.user.user.reset_password",
    "/api/method/frappe.desk.form.load.getdoctype",
    "/api/method/run_doc_method",
]


def authenticate():
    if not frappe.conf.get("block_endpoints"):
        return

    if frappe.form_dict.cmd:
        path = f"/api/method/{frappe.form_dict.cmd}"
    else:
        path = frappe.request.path
    user_type = frappe.db.get_value("User", frappe.session.user, "user_type")

    if user_type == "System User":
        return

    if not path.startswith("/api/"):
        return

    if path.startswith("/helpdesk") or path.startswith("/api/method/helpdesk."):
        return
    if path.startswith("/telephony") or path.startswith("/api/method/telephony."):
        return

    if is_server_script_path(path):
        return

    if is_custom_app_endpoint(path):
        return

    if path in ALLOWED_PATHS:
        return
    frappe.throw(f"Access not allowed for this URL: {path}", frappe.PermissionError)


def is_server_script_path(path):
    endpoint = path.split("/api/method/")[-1]
    if frappe.db.exists(
        "Server Script", {"script_type": "API", "api_method": endpoint, "disabled": 0}
    ):
        return True
    return False


def is_custom_app_endpoint(path):
    allowed_custom_endpoints = frappe.conf.get("allowed_custom_endpoints", [])

    if isinstance(allowed_custom_endpoints, str):
        try:
            parsed = json.loads(allowed_custom_endpoints)
            allowed_custom_endpoints = (
                parsed if isinstance(parsed, list) else [allowed_custom_endpoints]
            )
        except Exception:
            allowed_custom_endpoints = [allowed_custom_endpoints]

    for endpoint in allowed_custom_endpoints:  # noqa: SIM110
        if endpoint in path:
            return True
    return False
