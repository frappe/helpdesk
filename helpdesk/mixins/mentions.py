import frappe

from helpdesk.utils import extract_mentions


class HasMentions:
    def notify_mentions(self, original_content=None):
        """
        Extract mentions from `mentions_field`, and notify.
        `mentions_field` must have `HTML` content.
        """
        mentions_field = getattr(self, "mentions_field", None)
        if not mentions_field:
            return
        current_mentions = extract_mentions(self.get(mentions_field))
        if original_content:
            original_mentions = extract_mentions(original_content)
            original_emails = {m.email for m in original_mentions}
            # Only keep new mentions
            current_mentions = [
                m for m in current_mentions if m.email not in original_emails
            ]

        if not current_mentions:
            return

        if self.doctype == "HD Ticket Comment":
            already_notified = set(
                frappe.get_all(
                    "HD Notification",
                    filters={
                        "notification_type": "Mention",
                        "reference_comment": self.name,
                    },
                    pluck="user_to",
                )
            )
        else:
            already_notified = set()

        for mention in current_mentions:
            if mention.type == "team":
                users_to_notify = frappe.get_all(
                    "HD Team Member",
                    filters={"parent": mention.email},
                    pluck="user",
                )
            else:
                users_to_notify = [mention.email]

            for user_email in users_to_notify:
                if self.owner == user_email:
                    continue

                if user_email in already_notified:
                    continue

                values = frappe._dict(
                    doctype="HD Notification",
                    user_from=self.owner,
                    user_to=user_email,
                    notification_type="Mention",
                    message=self.content,
                )
                if self.doctype == "HD Ticket Comment":
                    values.reference_comment = self.name
                    values.reference_ticket = self.reference_ticket
                frappe.get_doc(values).insert()
                already_notified.add(user_email)
