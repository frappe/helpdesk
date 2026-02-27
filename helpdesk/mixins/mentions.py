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

        for mention in current_mentions:
            values = frappe._dict(
                doctype="HD Notification",
                user_from=self.owner,
                user_to=mention.email,
                notification_type="Mention",
                message=self.content,
            )
            # Why mention oneself?
            if values.user_from == values.user_to:
                continue
            # Only comment (in tickets) has mentions as of now
            if self.doctype == "HD Ticket Comment":
                values.reference_comment = self.name
                values.reference_ticket = self.reference_ticket
            if frappe.db.exists(
                "HD Notification",
                {
                    "reference_comment": self.name,
                    "user_to": mention.email,
                    "notification_type": "Mention",
                },
            ):
                # avoid loop of notification to quit at first mention
                continue
            frappe.get_doc(values).insert()
