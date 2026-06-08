"""
Unit tests for AWS SES Settings DocType schema validation
"""

import unittest
import frappe
from frappe.exceptions import ValidationError


class TestAWSSESSettingsSchema(unittest.TestCase):
    """Test AWS SES Settings validation rules"""

    def setUp(self):
        """Setup test environment"""
        # Create settings if not exists
        if not frappe.db.exists("AWS SES Settings", "AWS SES Settings"):
            settings = frappe.get_doc({
                "doctype": "AWS SES Settings",
                "enabled": 0,
            })
            settings.insert(ignore_permissions=True)
        else:
            # Reset to disabled
            settings = frappe.get_single("AWS SES Settings")
            settings.enabled = 0
            settings.save(ignore_permissions=True)

        frappe.db.commit()

    def test_enabled_requires_aws_region(self):
        """SES enabled without aws_region should fail"""
        settings = frappe.get_single("AWS SES Settings")
        settings.enabled = 1
        settings.aws_region = ""
        settings.default_sender_email = "sender@example.com"

        with self.assertRaises(ValidationError):
            settings.save()

    def test_enabled_requires_default_sender_email(self):
        """SES enabled without default_sender_email should fail"""
        settings = frappe.get_single("AWS SES Settings")
        settings.enabled = 1
        settings.aws_region = "us-east-1"
        settings.default_sender_email = ""

        with self.assertRaises(ValidationError):
            settings.save()

    def test_invalid_email_format(self):
        """Invalid email format should fail"""
        settings = frappe.get_single("AWS SES Settings")
        settings.enabled = 1
        settings.aws_region = "us-east-1"
        settings.default_sender_email = "not-an-email"

        with self.assertRaises(ValidationError):
            settings.save()

    def test_valid_configuration(self):
        """Valid configuration should save"""
        settings = frappe.get_single("AWS SES Settings")
        settings.enabled = 0  # Keep disabled for tests
        settings.aws_region = "us-east-1"
        settings.default_sender_email = "sender@example.com"
        settings.default_sender_name = "Test Sender"
        settings.retry_mode = "standard"
        settings.total_max_attempts = 3

        try:
            settings.save()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Valid config should not fail: {str(e)}")

    def test_explicit_credentials_require_access_key(self):
        """Explicit credentials without access_key_id should fail"""
        settings = frappe.get_single("AWS SES Settings")
        settings.enabled = 1
        settings.aws_region = "us-east-1"
        settings.default_sender_email = "sender@example.com"
        settings.use_explicit_credentials = 1
        settings.access_key_id = ""
        settings.secret_access_key = "secret123"

        with self.assertRaises(ValidationError):
            settings.save()

    def test_explicit_credentials_require_secret_key(self):
        """Explicit credentials without secret_access_key should fail"""
        settings = frappe.get_single("AWS SES Settings")
        settings.enabled = 1
        settings.aws_region = "us-east-1"
        settings.default_sender_email = "sender@example.com"
        settings.use_explicit_credentials = 1
        settings.access_key_id = "AKIATEST"
        settings.secret_access_key = ""

        with self.assertRaises(ValidationError):
            settings.save()
