#!/usr/bin/env python3
"""
AWS SES Configuration Script
Run this to configure AWS SES settings for the Helpdesk app
"""

import sys
import frappe


def configure_ses_settings(
    aws_region,
    default_sender_email,
    access_key_id,
    secret_access_key,
    default_sender_name="Helpdesk Support",
    enabled=False,
):
    """
    Configure AWS SES Settings

    Args:
        aws_region: AWS region (e.g., us-east-1)
        default_sender_email: Verified sender email in SES
        access_key_id: AWS Access Key ID
        secret_access_key: AWS Secret Access Key
        default_sender_name: Sender name (optional)
        enabled: Enable SES (default False for initial setup)
    """
    try:
        # Get or create settings
        if frappe.db.exists("AWS SES Settings", "AWS SES Settings"):
            settings = frappe.get_single("AWS SES Settings")
            print("✓ Found existing AWS SES Settings")
        else:
            settings = frappe.get_doc({"doctype": "AWS SES Settings"})
            print("✓ Creating new AWS SES Settings")

        # Update settings
        settings.enabled = int(enabled)
        settings.aws_region = aws_region
        settings.default_sender_email = default_sender_email
        settings.default_sender_name = default_sender_name
        settings.retry_mode = "standard"
        settings.total_max_attempts = 3

        # Configure explicit credentials
        settings.use_explicit_credentials = 1
        settings.access_key_id = access_key_id
        settings.set("secret_access_key", secret_access_key)

        # Save
        settings.save(ignore_permissions=True)
        frappe.db.commit()

        print("\n✅ AWS SES Settings configured successfully!")
        print(f"   Region: {aws_region}")
        print(f"   Sender Email: {default_sender_email}")
        print(f"   Sender Name: {default_sender_name}")
        print(f"   Enabled: {'Yes' if enabled else 'No (configure first, enable later)'}")

        if not enabled:
            print("\n⚠️  SES is currently DISABLED")
            print("   To enable:")
            print("   1. Verify sender email in AWS SES Console")
            print("   2. Test configuration with healthcheck:")
            print("      bench --site <site> execute helpdesk.email.aws_ses_healthcheck.run")
            print("   3. Enable SES in AWS SES Settings form")

        return True

    except Exception as e:
        print(f"\n❌ Error configuring AWS SES Settings: {str(e)}")
        frappe.log_error(f"SES configuration error: {str(e)}", "AWS SES Setup Error")
        return False


if __name__ == "__main__":
    # This script should be called via bench execute
    print("Use: bench --site <site> execute helpdesk.configure_ses.configure_ses_settings --kwargs \"{'aws_region': '...', ...}\"")
