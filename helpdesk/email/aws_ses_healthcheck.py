"""
AWS SES Healthcheck
Verifies SES configuration, hook ownership, and readiness
"""

import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def run():
    """
    Run SES readiness healthcheck
    Restricted to System Manager role
    """
    # Check permissions
    if not frappe.has_permission("AWS SES Settings", "read"):
        frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

    from helpdesk.email.aws_ses_config import get_ses_config, mask_email

    result = {
        "status": "unknown",
        "checks": [],
        "remediation": [],
    }

    try:
        # Load config
        config = get_ses_config()

        # Check 1: Enabled status
        result["checks"].append({
            "name": "SES Enabled",
            "status": "pass" if config.enabled else "info",
            "value": config.enabled,
            "message": "SES is enabled" if config.enabled else "SES is disabled (using native Email Account)"
        })

        if not config.enabled:
            result["status"] = "disabled"
            result["checks"].append({
                "name": "Native Email Account",
                "status": "info",
                "message": "Check that native Email Account is configured for outgoing email"
            })
            return result

        # Check 2: Required settings
        required_checks = [
            ("AWS Region", config.aws_region),
            ("Default Sender Email", mask_email(config.default_sender_email)),
        ]

        for check_name, check_value in required_checks:
            result["checks"].append({
                "name": check_name,
                "status": "pass" if check_value else "fail",
                "value": check_value,
                "message": f"{check_name}: {check_value}" if check_value else f"{check_name} is missing"
            })

            if not check_value:
                result["remediation"].append(f"Configure {check_name} in AWS SES Settings")

        # Check 3: Optional settings
        result["checks"].append({
            "name": "Configuration Set",
            "status": "info",
            "value": config.configuration_set_name or "Not set",
            "message": f"Configuration Set: {config.configuration_set_name or 'Not set (optional)'}"
        })

        # Check 4: Hook ownership
        hook_target = frappe.get_hooks("override_email_send")
        expected_hook = "helpdesk.email.aws_ses_override.send"

        if isinstance(hook_target, list):
            hook_target = hook_target[0] if hook_target else None

        hook_matches = hook_target == expected_hook

        result["checks"].append({
            "name": "Email Send Hook",
            "status": "pass" if hook_matches else "fail",
            "value": hook_target,
            "message": f"Hook target: {hook_target}"
        })

        if not hook_matches:
            result["remediation"].append(
                f"Hook mismatch: expected '{expected_hook}', got '{hook_target}'. "
                "Check hooks.py for conflicts."
            )

        # Check 5: Email Queue controller
        override_classes = frappe.get_hooks("override_doctype_class") or {}

        # Handle both list and dict formats
        if isinstance(override_classes, list):
            override_classes = override_classes[0] if override_classes else {}

        # Handle case where the value itself might be a list
        email_queue_class = override_classes.get("Email Queue", "")
        if isinstance(email_queue_class, list):
            email_queue_class = email_queue_class[0] if email_queue_class else ""

        expected_class = "helpdesk.email.email_queue_override.SesAwareEmailQueue"
        class_matches = email_queue_class == expected_class

        result["checks"].append({
            "name": "Email Queue Controller",
            "status": "pass" if class_matches else "warning",
            "value": email_queue_class or "Default (Frappe)",
            "message": f"Email Queue class: {email_queue_class or 'Default (Frappe)'}"
        })

        if not class_matches and email_queue_class:
            result["remediation"].append(
                f"Email Queue controller mismatch: expected '{expected_class}', got '{email_queue_class}'"
            )

        # Check 6: AWS credentials
        try:
            ses_client = _build_test_ses_client(config)
            result["checks"].append({
                "name": "AWS Credentials",
                "status": "pass",
                "message": "Credentials resolved successfully"
            })
        except Exception as e:
            result["checks"].append({
                "name": "AWS Credentials",
                "status": "fail",
                "message": f"Credential error: {str(e)}"
            })
            result["remediation"].append(
                "Check AWS credentials: IAM role, environment variables, or explicit credentials in settings"
            )

        # Check 7: SES quota
        try:
            ses_client = _build_test_ses_client(config)
            quota_response = ses_client.get_send_quota()

            result["checks"].append({
                "name": "SES Quota",
                "status": "pass",
                "value": {
                    "Max24HourSend": quota_response.get("Max24HourSend"),
                    "MaxSendRate": quota_response.get("MaxSendRate"),
                    "SentLast24Hours": quota_response.get("SentLast24Hours"),
                },
                "message": f"Daily limit: {quota_response.get('Max24HourSend')}, "
                           f"Rate: {quota_response.get('MaxSendRate')}/sec, "
                           f"Sent today: {quota_response.get('SentLast24Hours')}"
            })
        except Exception as e:
            result["checks"].append({
                "name": "SES Quota",
                "status": "fail",
                "message": f"Could not fetch quota: {str(e)}"
            })
            result["remediation"].append(
                "Check SES permissions: ensure IAM policy allows ses:GetSendQuota"
            )

        # Check 8: SES v2 client (for large messages)
        try:
            sesv2_client = _build_test_sesv2_client(config)
            result["checks"].append({
                "name": "SES v2 Client",
                "status": "pass",
                "message": "SES v2 client constructed successfully (for messages >10MB)"
            })
        except Exception as e:
            result["checks"].append({
                "name": "SES v2 Client",
                "status": "warning",
                "message": f"SES v2 client error: {str(e)} (only needed for messages >10MB)"
            })

        # Determine overall status
        failed_checks = [c for c in result["checks"] if c["status"] == "fail"]
        if failed_checks:
            result["status"] = "not_ready"
        elif result["remediation"]:
            result["status"] = "not_ready"
        else:
            result["status"] = "ready"

    except Exception as e:
        result["status"] = "error"
        result["checks"].append({
            "name": "Healthcheck Error",
            "status": "fail",
            "message": str(e)
        })
        frappe.log_error(f"SES healthcheck error: {str(e)}", "SES Healthcheck Error")

    return result


def _build_test_ses_client(config):
    """Build SES client for testing"""
    import boto3
    from botocore.config import Config

    retry_config = Config(
        retries={
            'mode': config.retry_mode,
            'total_max_attempts': config.total_max_attempts,
        }
    )

    client_params = {
        'service_name': 'ses',
        'region_name': config.aws_region,
        'config': retry_config,
    }

    if config.endpoint_url:
        client_params['endpoint_url'] = config.endpoint_url

    if config.use_explicit_credentials:
        client_params['aws_access_key_id'] = config.access_key_id
        client_params['aws_secret_access_key'] = config.secret_access_key
        if config.session_token:
            client_params['aws_session_token'] = config.session_token

    return boto3.client(**client_params)


def _build_test_sesv2_client(config):
    """Build SES v2 client for testing"""
    import boto3
    from botocore.config import Config

    retry_config = Config(
        retries={
            'mode': config.retry_mode,
            'total_max_attempts': config.total_max_attempts,
        }
    )

    client_params = {
        'service_name': 'sesv2',
        'region_name': config.aws_region,
        'config': retry_config,
    }

    if config.endpoint_url:
        client_params['endpoint_url'] = config.endpoint_url

    if config.use_explicit_credentials:
        client_params['aws_access_key_id'] = config.access_key_id
        client_params['aws_secret_access_key'] = config.secret_access_key
        if config.session_token:
            client_params['aws_session_token'] = config.session_token

    return boto3.client(**client_params)
