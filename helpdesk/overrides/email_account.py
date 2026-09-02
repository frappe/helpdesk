import re
from email import message_from_string

import frappe
from frappe import _
from frappe.core.doctype.communication.communication import Communication
from frappe.email.doctype.email_account.email_account import EmailAccount
from frappe.email.doctype.email_queue.email_queue import EmailQueue
from frappe.email.receive import InboundMail
from frappe.utils import parse_addr


def auto_generated_reason(msg) -> str | None:
    """Why this mail is machine-generated (bounce or autoresponder), else None.

    One such mail can start three different loops: opening a ticket acks
    raised_by straight back to the address that just bounced
    (HD Ticket.after_insert), threading onto a portal ticket makes frappe CC the
    parent doc's owner -- the same dead address -- on every inbound mail
    (mail_cc), and an account with enable_auto_reply answers mailer-daemon.

    X-Auto-Generated only catches helpdesk's own acks, which stamp it. Real
    bounces announce themselves with RFC 3834 Auto-Submitted, the RFC 3464
    report type, or the RFC 5321 null return-path.
    """
    if msg.get("X-Auto-Generated"):
        return "X-Auto-Generated"

    # bounce markers first, so the reason distinguishes a dead address from a
    # mere autoresponder (a DSN usually carries Auto-Submitted too)

    # RFC 3464 delivery status notification -- survives a stripped Return-Path
    if (
        msg.get_content_type() == "multipart/report"
        and msg.get_param("report-type") == "delivery-status"
    ):
        return "delivery status notification"

    # bounces MUST carry a null envelope sender (RFC 5321 §6.1)
    if (msg.get("Return-Path") or "").strip() == "<>":
        return "null return-path"

    # RFC 3834: "no" is the only human-sent value, and it may carry parameters
    auto_submitted = (msg.get("Auto-Submitted") or "no").split(";")[0].strip().lower()
    if auto_submitted != "no":
        return f"Auto-Submitted: {auto_submitted}"

    return None


def _failed_recipient(msg) -> str | None:
    """The address a DSN reports as undeliverable, if it names one."""
    for part in msg.walk():
        if part.get_content_type() != "message/delivery-status":
            continue
        for status_block in part.get_payload():
            recipient = status_block.get("Final-Recipient") or ""
            if ";" in recipient:
                return recipient.split(";", 1)[1].strip()
    return None


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
    def handle_bad_emails(self, uid, raw, reason):
        """Same record as the framework version, without its use_imap gate.

        POP3 and Frappe Mail hit the same drop paths as IMAP, and nothing
        that reads Unhandled Email is IMAP-specific -- a silent drop would
        hide a misclassified customer mail, so record on every transport.
        """
        try:
            raw_str = (
                raw.decode("ASCII", "replace")
                if isinstance(raw, bytes)
                else raw.encode(errors="replace").decode()
            )
            message_id = message_from_string(raw_str).get("Message-ID")
        except Exception:
            raw_str = message_id = "can't be parsed"

        frappe.get_doc(
            {
                "doctype": "Unhandled Email",
                "raw": raw_str,
                "uid": uid,
                "reason": reason,
                "message_id": message_id,
                "email_account": self.name,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()

    def notify_ticket_of_parked_mail(self, message, msg, reason):
        """Parked mail no longer threads onto tickets, so agents would never
        learn that a reply bounced or that the customer is out of office.
        Leave an internal comment on the ticket the mail belongs to."""
        communication = CustomInboundMail(message, self).parent_communication()
        if not communication or communication.reference_doctype != "HD Ticket":
            return

        if reason.startswith("Auto-Submitted"):
            sender = parse_addr(msg.get("From") or "")[1]
            content = _("Auto-reply received from {0}.").format(
                sender or _("the customer")
            )
        else:
            recipient = _failed_recipient(msg)
            content = (
                _(
                    "Delivery failed: the reply to this ticket could not be delivered to {0}."
                ).format(recipient)
                if recipient
                else _(
                    "Delivery failed: the reply to this ticket could not be delivered."
                )
            )

        comment = frappe.new_doc("HD Ticket Comment")
        # not frappe.session.user: no human acted, even on a manual pull
        comment.commented_by = "Administrator"
        comment.reference_ticket = communication.reference_name
        comment.content = content
        comment.save(ignore_permissions=True)

    def get_inbound_mails(self) -> list[InboundMail]:
        """retrive and return inbound mails."""
        mails = []

        def process_mail(messages, append_to=None):
            for index, message in enumerate(messages.get("latest_messages", [])):
                try:
                    _msg = message_from_string(
                        message.decode("utf-8", errors="replace")
                    )

                    uid = (
                        messages["uid_list"][index]
                        if messages.get("uid_list")
                        else None
                    )

                    # Important: auto-generated mail must never reach a ticket, it
                    # starts a mail loop. The fetch already marked it seen, so park
                    # it in Unhandled Email instead of dropping it without a trace.
                    if reason := auto_generated_reason(_msg):
                        self.handle_bad_emails(uid, message, reason)
                        # our own looped-back ack carries no news for agents
                        if reason != "X-Auto-Generated":
                            try:
                                self.notify_ticket_of_parked_mail(message, _msg, reason)
                            except Exception:
                                frappe.log_error(
                                    title=_("Could not note parked mail on ticket"),
                                    message=frappe.get_traceback(),
                                )
                        continue

                    seen_status = messages.get("seen_status", {}).get(uid)
                    if self.email_sync_option != "UNSEEN" or seen_status != "SEEN":
                        _inbound_mail = CustomInboundMail(
                            message,
                            self,
                            frappe.safe_decode(uid),
                            seen_status,
                            append_to,
                        )
                        mails.append(_inbound_mail)
                except Exception as e:
                    # Log the error but continue processing other emails
                    frappe.log_error(
                        title=_(
                            "Error processing email at index {0}, message: {1}"
                        ).format(index, e),
                        message=frappe.get_traceback(),
                    )
                    self.handle_bad_emails(index, message, frappe.get_traceback())
                    continue

        if not self.enable_incoming:
            return []

        try:
            if self.service == "Frappe Mail":
                frappe_mail_client = self.get_frappe_mail_client()
                messages = frappe_mail_client.pull_raw(
                    last_received_at=self.last_synced_at
                )
                process_mail(messages)
                self.db_set(
                    "last_synced_at",
                    messages["last_received_at"],
                    update_modified=False,
                )
            else:
                email_sync_rule = self.build_email_sync_rule()
                email_server = self.get_incoming_server(
                    in_receive=True, email_sync_rule=email_sync_rule
                )
                if self.use_imap:
                    # process all given imap folder
                    for folder in self.imap_folder:
                        if email_server.select_imap_folder(folder.folder_name):
                            email_server.settings["uid_validity"] = folder.uidvalidity
                            messages = (
                                email_server.get_messages(
                                    folder=f'"{folder.folder_name}"'
                                )
                                or {}
                            )
                            process_mail(messages, folder.append_to)
                else:
                    # process the pop3 account
                    messages = email_server.get_messages() or {}
                    process_mail(messages)

                # close connection to mailserver
                email_server.logout()
        except Exception:
            self.log_error(
                title=_("Error while connecting to email account {0}").format(self.name)
            )
            return []

        return mails
