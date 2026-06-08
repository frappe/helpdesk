"""
AWS SES Email Override
Central transport layer for sending emails through AWS SES or native Frappe Email Account
"""

import frappe
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send(queue_doc, sender: str, recipient: str, message: bytes):
    """
    Central email send hook (override_email_send)
    Routes emails through SES or native transport based on settings

    Args:
        queue_doc: Email Queue document
        sender: Sender email address
        recipient: Recipient email address
        message: Raw MIME message bytes
    """
    from helpdesk.email.aws_ses_config import get_ses_config, mask_email

    # Load configuration
    config = get_ses_config()

    # Route based on enabled flag
    if not config.enabled:
        # SES disabled - use native Frappe Email Account
        return _send_via_native_transport(queue_doc, sender, recipient, message)

    # SES enabled - validate and send through SES
    try:
        return _send_via_ses(queue_doc, sender, recipient, message, config)
    except Exception as e:
        # Log error with masked recipient
        frappe.log_error(
            title=f"AWS SES Send Failed - Queue: {queue_doc.name}",
            message=f"Recipient: {mask_email(recipient)}\nError: {str(e)}"
        )
        # Re-raise to preserve Email Queue retry behavior
        raise


def _send_via_ses(queue_doc, sender: str, recipient: str, message: bytes, config):
    """Send email through AWS SES"""
    from helpdesk.email.aws_ses_config import mask_email

    # Skip external sends in test mode
    if frappe.flags.in_test and not frappe.flags.enable_ses_in_tests:
        frappe.msgprint(f"Test mode: Would send via SES to {mask_email(recipient)}")
        return

    # Validate runtime config
    if not config.aws_region or not config.default_sender_email:
        raise ValueError("SES is enabled but configuration is incomplete")

    # Get message size
    message_size_mb = len(message) / (1024 * 1024)

    # Check size limits
    if message_size_mb > 40:
        raise ValueError(f"Message size {message_size_mb:.2f}MB exceeds SES limit of 40MB")

    # Build SES client
    ses_client = _build_ses_client(config, message_size_mb)

    # Process sender/reply-to
    from_addr = config.default_sender_email
    reply_to = None

    # Parse original message to preserve reply-to
    try:
        from email import message_from_bytes
        original_msg = message_from_bytes(message)
        original_from = original_msg.get('From', '')
        original_reply_to = original_msg.get('Reply-To', '')

        # If original From differs and no Reply-To, set Reply-To to original From
        if original_from and original_from != from_addr and not original_reply_to:
            reply_to = original_from
        elif original_reply_to:
            reply_to = original_reply_to

    except Exception as e:
        frappe.log_error(f"Error parsing message headers: {str(e)}", "SES Header Parse Error")

    # Send based on message size
    if message_size_mb <= 10:
        # Use SES v1 send_raw_email
        message_id = _send_ses_v1(ses_client, config, from_addr, recipient, message, reply_to)
        transport = "sesv1"
    else:
        # Use SES v2 send_email (raw)
        message_id = _send_ses_v2(ses_client, config, from_addr, recipient, message, reply_to)
        transport = "sesv2"

    # Log success with masked recipient
    frappe.logger().info(
        f"SES send success - Queue: {queue_doc.name}, "
        f"Transport: {transport}, "
        f"Recipient: {mask_email(recipient)}, "
        f"MessageID: {message_id}"
    )


def _send_ses_v1(ses_client, config, from_addr, recipient, message, reply_to):
    """Send via SES v1 send_raw_email (<=10MB)"""
    params = {
        'Source': from_addr,
        'Destinations': [recipient],
        'RawMessage': {'Data': message},
    }

    if config.configuration_set_name:
        params['ConfigurationSetName'] = config.configuration_set_name

    response = ses_client.send_raw_email(**params)
    return response.get('MessageId', '')


def _send_ses_v2(ses_client, config, from_addr, recipient, message, reply_to):
    """Send via SES v2 send_email (>10MB, <=40MB)"""
    # Note: SES v2 uses sesv2 client
    sesv2_client = _build_sesv2_client(config)

    params = {
        'FromEmailAddress': from_addr,
        'Destination': {
            'ToAddresses': [recipient],
        },
        'Content': {
            'Raw': {'Data': message}
        },
    }

    if config.configuration_set_name:
        params['ConfigurationSetName'] = config.configuration_set_name

    response = sesv2_client.send_email(**params)
    return response.get('MessageId', '')


def _build_ses_client(config, message_size_mb=0):
    """Build SES v1 client with retry configuration"""
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

    # Add explicit credentials if configured
    if config.use_explicit_credentials:
        client_params['aws_access_key_id'] = config.access_key_id
        client_params['aws_secret_access_key'] = config.secret_access_key
        if config.session_token:
            client_params['aws_session_token'] = config.session_token

    return boto3.client(**client_params)


def _build_sesv2_client(config):
    """Build SES v2 client for large messages"""
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


def _send_via_native_transport(queue_doc, sender: str, recipient: str, message: bytes):
    """
    Send via native Frappe Email Account
    This is the fallback when SES is disabled
    """
    from helpdesk.email.aws_ses_config import mask_email

    # Check if native Email Account exists
    if not frappe.db.exists("Email Account", {"enable_outgoing": 1, "default_outgoing": 1}):
        raise ValueError(
            "SES is disabled but no native outgoing Email Account is configured. "
            "Please configure an Email Account or enable AWS SES."
        )

    # Use native Frappe email send
    # Import at runtime to avoid circular dependencies
    from frappe.email.doctype.email_queue.email_queue import EmailQueue

    # Get the original send method (before override)
    # This delegates to Frappe's SMTP/Mail service
    try:
        # Call native Email Queue send
        native_queue = EmailQueue(queue_doc.name)
        native_queue.send(sender, recipient, message)

        frappe.logger().info(
            f"Native send success - Queue: {queue_doc.name}, "
            f"Recipient: {mask_email(recipient)}"
        )
    except Exception as e:
        frappe.log_error(
            title=f"Native Email Send Failed - Queue: {queue_doc.name}",
            message=f"Recipient: {mask_email(recipient)}\nError: {str(e)}"
        )
        raise
