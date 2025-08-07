from email import message_from_string

import frappe
from frappe import _
from frappe.email.doctype.email_account.email_account import EmailAccount
from frappe.email.receive import InboundMail


class CustomEmailAccount(EmailAccount):
    def get_inbound_mails(self) -> list[InboundMail]:
        """retrive and return inbound mails."""
        mails = []

        def process_mail(messages, append_to=None):
            for index, message in enumerate(messages.get("latest_messages", [])):
                _msg = message_from_string(message.decode())
                # Important: If the email is auto-generated, we do not create a ticket
                if _msg.get("X-Auto-Generated"):
                    continue

                uid = messages["uid_list"][index] if messages.get("uid_list") else None
                seen_status = messages.get("seen_status", {}).get(uid)
                if self.email_sync_option != "UNSEEN" or seen_status != "SEEN":
                    # only append the emails with status != 'SEEN' if sync option is set to 'UNSEEN'
                    _inbound_mail = InboundMail(
                        message, self, frappe.safe_decode(uid), seen_status, append_to
                    )
                    mails.append(_inbound_mail)

        if not self.enable_incoming:
            return []

        try:
            if self.service == "Frappe Mail":
                frappe_mail_client = self.get_frappe_mail_client()
                messages = frappe_mail_client.pull_raw(
                    last_synced_at=self.last_synced_at
                )
                process_mail(messages)
                self.db_set(
                    "last_synced_at", messages["last_synced_at"], update_modified=False
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
