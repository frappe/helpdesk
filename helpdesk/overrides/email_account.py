import re

import frappe
from frappe import _
from frappe.core.doctype.communication.communication import Communication
from frappe.email.doctype.email_account.email_account import EmailAccount
from frappe.email.doctype.email_queue.email_queue import EmailQueue
from frappe.email.receive import InboundMail


class CustomInboundMail(InboundMail):
    """
    Extend InboundMail with robust thread stitching for forwarded emails.
       1. Run the standard Frappe parent_communication lookups first (In-Reply-To → Communication, EmailQueue, communication-name fallback)
       2. If still no parent, use the References header from emails, which may contain multiple message IDs in a thread
    """

    def _find_communication_by_message_id(self, msg_id: str):
        """Return a Communication for msg_id, checking both Communication and EmailQueue."""
        # Direct hit: incoming email stored its message_id on Communication
        comm = Communication.find_one_by_filters(
            message_id=msg_id, order_by="creation DESC"
        )
        if comm:
            return comm

        # Outgoing email: message_id lives in EmailQueue, not on Communication
        eq = EmailQueue.find_one_by_filters(message_id=msg_id)
        if eq and eq.communication:
            return Communication.find(eq.communication, ignore_error=True) or None

        return None

    def parent_communication(self):
        # Respect cached result from any prior call on this instance
        if self._parent_communication is not None:
            return self._parent_communication

        # Run the standard Frappe lookup method first. Checks for finding in reply to in Communication then if not found it looks in EmailQueue
        result = super().parent_communication()
        if result:
            return result

        # fallback: use the References header from emails
        references_raw = self.mail.get("References") or ""
        ref_ids = re.findall(r"<([^>]+)>", references_raw)

        for ref_id in reversed(ref_ids):
            communication = self._find_communication_by_message_id(ref_id)
            if communication:
                self._parent_communication = communication
                return self._parent_communication

        self._parent_communication = ""
        return self._parent_communication


class CustomEmailAccount(EmailAccount):
    def get_inbound_mails(self) -> list[InboundMail]:
        """Return the framework's inbound mails, filtered and re-wrapped.

        This used to be a full copy of `EmailAccount.get_inbound_mails`, which meant every
        fix the framework made to the fetch loop was silently lost on any site where
        helpdesk is installed -- including the per-folder IMAP UID cursor, whose absence
        made each poll retrieve only the newest message of every folder. Delegate the
        fetching and keep only what is specific to helpdesk: skipping auto-generated
        mails, and threading through CustomInboundMail.
        """
        mails = []

        for mail in super().get_inbound_mails():
            try:
                if mail.mail.get("X-Auto-Generated"):
                    # Important: If the email is auto-generated, we do not create a ticket
                    continue

                mails.append(
                    CustomInboundMail(
                        mail.raw_message,
                        self,
                        mail.uid,
                        mail.seen_status,
                        mail.append_to,
                    )
                )
            except Exception as e:
                # Log the error but continue processing other emails
                frappe.log_error(
                    title=_("Error processing email {0}, message: {1}").format(mail.uid, e),
                    message=frappe.get_traceback(),
                )
                self.handle_bad_emails(mail.uid, mail.raw_message, frappe.get_traceback())
                continue

        return mails
