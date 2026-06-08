"""
Unit tests for AWS SES Configuration
"""

import unittest
import frappe
from helpdesk.email.aws_ses_config import get_ses_config, mask_email, clear_config_cache


class TestAWSSESConfig(unittest.TestCase):
    """Test AWS SES configuration loading and validation"""

    def setUp(self):
        """Setup test environment"""
        clear_config_cache()

    def tearDown(self):
        """Cleanup"""
        clear_config_cache()

    def test_disabled_config_when_doctype_missing(self):
        """Config returns disabled when DocType doesn't exist"""
        # This test simulates fresh install
        config = get_ses_config()
        self.assertFalse(config.enabled)

    def test_mask_email(self):
        """Test email masking for privacy-safe logging"""
        masked = mask_email("user@example.com")
        self.assertIn("***", masked)
        self.assertNotIn("user", masked)

        masked2 = mask_email("test@domain.org")
        self.assertIn("***", masked2)
        self.assertIn("org", masked2)

    def test_mask_invalid_email(self):
        """Test masking invalid email"""
        masked = mask_email("not-an-email")
        self.assertEqual(masked, "***")

        masked2 = mask_email("")
        self.assertEqual(masked2, "***")
