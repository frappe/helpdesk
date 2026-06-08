# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.model.document import Document


class AWSSESSettings(Document):
    def validate(self):
        """Validate AWS SES settings"""
        if self.enabled:
            self.validate_required_fields()
            self.validate_email_format()
            self.validate_retry_config()
            self.validate_credentials()

    def validate_required_fields(self):
        """Ensure required fields are present when enabled"""
        if not self.aws_region:
            frappe.throw("AWS Region is required when SES is enabled")

        if not self.default_sender_email:
            frappe.throw("Default Sender Email is required when SES is enabled")

    def validate_email_format(self):
        """Validate email address format"""
        if self.default_sender_email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.default_sender_email):
                frappe.throw(f"Invalid email format: {self.default_sender_email}")

    def validate_retry_config(self):
        """Validate retry configuration"""
        valid_retry_modes = ['standard', 'adaptive', 'legacy']
        if self.retry_mode and self.retry_mode not in valid_retry_modes:
            frappe.throw(f"Retry mode must be one of: {', '.join(valid_retry_modes)}")

        if self.total_max_attempts and self.total_max_attempts < 1:
            frappe.throw("Total Max Attempts must be at least 1")

    def validate_credentials(self):
        """Validate explicit credentials if enabled"""
        if self.use_explicit_credentials:
            if not self.access_key_id:
                frappe.throw("Access Key ID is required when using explicit credentials")

            if not self.secret_access_key:
                frappe.throw("Secret Access Key is required when using explicit credentials")

    def on_update(self):
        """Clear config cache when settings are updated"""
        from helpdesk.email.aws_ses_config import clear_config_cache
        clear_config_cache()
