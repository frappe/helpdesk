"""
SES Email Account Decoupler
Provides synthetic Email Account for MIME generation when SES is enabled
"""

import frappe
from frappe import _


class SyntheticEmailAccount:
    """
    Synthetic Email Account-like object for SES mode
    Prevents QueueBuilder from failing when no native Email Account exists
    """

    def __init__(self, config):
        self.email_id = config.default_sender_email
        self.name = "AWS SES"
        self.email_account_name = "AWS SES"
        self.default_sender = config.default_sender_email
        self.sender = config.default_sender_name or config.default_sender_email
        self.enable_outgoing = 1
        self.smtp_server = "ses.amazonaws.com"
        self.use_tls = 1
        self.port = 587
        # Minimal fields to satisfy MIME generation
        self.always_use_account_email_id_as_sender = 0
        self.always_use_account_name_as_sender_name = 0


def get_email_account_for_ses():
    """
    Get synthetic Email Account when SES is enabled
    Called by QueueBuilder patch
    """
    from helpdesk.email.aws_ses_config import get_ses_config

    config = get_ses_config()

    if not config.enabled:
        # SES disabled - return None to use native resolution
        return None

    # Return synthetic account
    return SyntheticEmailAccount(config)


def patch_queue_builder():
    """
    Patch QueueBuilder to use synthetic Email Account in SES mode
    This prevents native Email Account resolution failures
    """
    from helpdesk.email.aws_ses_config import get_ses_config

    config = get_ses_config()

    if not config.enabled:
        # SES disabled - don't patch
        return

    # Monkey-patch frappe.email.queue.get_outgoing_email_account
    try:
        import frappe.email.queue as email_queue_module

        original_get_outgoing = getattr(
            email_queue_module,
            'get_outgoing_email_account',
            None
        )

        if original_get_outgoing:
            def ses_aware_get_outgoing(*args, **kwargs):
                """Wrapper that returns synthetic account in SES mode"""
                config = get_ses_config()
                if config.enabled:
                    return get_email_account_for_ses()
                return original_get_outgoing(*args, **kwargs)

            # Apply patch
            email_queue_module.get_outgoing_email_account = ses_aware_get_outgoing
            frappe.logger().info("QueueBuilder patched for SES mode")

    except Exception as e:
        frappe.log_error(f"Failed to patch QueueBuilder: {str(e)}", "SES QueueBuilder Patch Error")


def unpatch_queue_builder():
    """
    Remove QueueBuilder patch (for rollback)
    """
    try:
        import frappe.email.queue as email_queue_module
        # Reload module to restore original
        import importlib
        importlib.reload(email_queue_module)
        frappe.logger().info("QueueBuilder patch removed")
    except Exception as e:
        frappe.log_error(f"Failed to unpatch QueueBuilder: {str(e)}", "SES QueueBuilder Unpatch Error")
