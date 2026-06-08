"""
SES-Aware Email Queue Override
Prevents native outgoing server prefetch when SES is enabled
"""

import frappe
from frappe.email.doctype.email_queue.email_queue import EmailQueue


class SesAwareEmailQueue(EmailQueue):
    """
    Email Queue controller that works with AWS SES override
    Skips native Email Account prefetch when SES is enabled
    """

    def send(self, is_background_task=False):
        """
        Override send to handle SES mode
        """
        from helpdesk.email.aws_ses_config import get_ses_config

        config = get_ses_config()

        if not config.enabled:
            # SES disabled - use native send
            return super().send(is_background_task=is_background_task)

        # SES enabled - bypass native outgoing server check
        return self._send_with_ses(is_background_task)

    def _send_with_ses(self, is_background_task=False):
        """
        Send through SES without native Email Account prefetch
        """
        from frappe.utils import validate_email_address

        if self.status not in ("Not Sent", "Partially Sent"):
            # Prevent duplicate sends
            return

        # Test mode handling
        if frappe.flags.in_test and not frappe.flags.enable_ses_in_tests:
            self.db_set("status", "Sent")
            return

        # Get recipients from child table
        recipients = []
        for recipient_row in self.recipients:
            if recipient_row.recipient:
                recipients.append(recipient_row.recipient)

        frappe.logger().info(f"[SES Queue] Found {len(recipients)} recipients for queue {self.name}")

        if not recipients:
            frappe.throw("No recipients found in Email Queue")

        for recipient in recipients:
            if not recipient:
                continue

            frappe.logger().info(f"[SES Queue] Processing recipient: {recipient}")

            # Validate email
            try:
                validate_email_address(recipient.strip(), throw=True)
                frappe.logger().info(f"[SES Queue] Email validation passed for {recipient}")
            except Exception as e:
                frappe.logger().error(f"[SES Queue] Email validation failed for {recipient}: {e}")
                self._update_recipient_status(recipient, "Invalid", str(e))
                continue

            # Send through the override_email_send hook (aws_ses_override.send)
            try:
                frappe.logger().info(f"[SES Queue] Calling _send_email for {recipient}")
                # Call the parent class's _send method which triggers the override hook
                self._send_email(recipient)
                frappe.logger().info(f"[SES Queue] _send_email completed successfully for {recipient}")
                self._update_recipient_status(recipient, "Sent")

            except Exception as e:
                frappe.logger().error(f"[SES Queue] Error sending to {recipient}: {e}")
                self._update_recipient_status(recipient, "Error", str(e))
                frappe.log_error(
                    title=f"Email Queue Send Error - {self.name}",
                    message=f"Recipient: {recipient}\nError: {str(e)}"
                )

        # Update overall status
        frappe.logger().info(f"[SES Queue] Updating overall status for queue {self.name}")
        self._update_overall_status()

    def _send_email(self, recipient):
        """Send email to a single recipient using the parent class method"""
        from frappe.utils import get_formatted_email

        frappe.logger().info(f"[SES Queue] Starting _send_email for {recipient}")

        # Get the pre-built MIME message from the queue
        # The message is already complete with headers, body, etc.
        message = self.message

        # Replace the placeholder recipient with actual recipient
        if isinstance(message, str):
            message = message.replace("<!--recipient-->", recipient)
            message = message.encode('utf-8')
        elif isinstance(message, bytes):
            message = message.replace(b"<!--recipient-->", recipient.encode('utf-8'))

        frappe.logger().info(f"[SES Queue] Message prepared, size: {len(message)} bytes")

        # Get sender
        sender = get_formatted_email(self.sender)
        frappe.logger().info(f"[SES Queue] Sender: {sender}, calling aws_ses_override.send")

        # Call the override hook directly
        from helpdesk.email.aws_ses_override import send
        send(self, sender, recipient, message)

        frappe.logger().info(f"[SES Queue] aws_ses_override.send completed for {recipient}")

    def _update_recipient_status(self, recipient, status, error=None):
        """Update individual recipient status"""
        for recipient_row in self.recipients:
            if recipient_row.recipient == recipient:
                recipient_row.db_set("status", status, update_modified=False)
                if error:
                    recipient_row.db_set("error", error, update_modified=False)
                break

    def _update_overall_status(self):
        """Update overall Email Queue status based on recipient results"""
        # Count sent/error recipients
        sent_count = 0
        error_count = 0

        for recipient_row in self.recipients:
            if recipient_row.status == "Sent":
                sent_count += 1
            elif recipient_row.status == "Error":
                error_count += 1

        total = len(self.recipients)

        if sent_count == total:
            self.db_set("status", "Sent")
        elif sent_count > 0:
            self.db_set("status", "Partially Sent")
        elif error_count == total:
            self.db_set("status", "Error")
