import frappe
from frappe.model.document import Document


class HDNotification(Document):
    def format_message(self):
        user_from = self.get_from()
        if self.notification_type == "Mention":
            if self.reference_comment:
                return f"{user_from} mentioned you in a comment"
            return f"{user_from} mentioned you"
        return ""

    def get_from(self):
        return frappe.db.get_value(
            "User", {"name": self.user_from}, fieldname="full_name"
        )

    def get_button_label(self):
        if self.reference_comment:
            return "See Comment"
        return "Visit"

    def get_url(self):
        res = "/helpdesk"
        if self.reference_ticket:
            res += "/tickets/" + str(self.reference_ticket)
        if self.reference_comment:
            res += "#" + self.reference_comment
        return frappe.utils.get_url(res)

    def parse_html(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(self.message, "html.parser")
        if soup.find("img"):
            img = soup.find("img")
            img["src"] = ("").join([frappe.utils.get_url(), img["src"]])
            return str(soup)
        return str(soup)

    def get_args(self):
        if self.notification_type == "Mention":
            return {
                "title": self.format_message(),
                "button_label": self.get_button_label(),
                "callback_url": self.get_url(),
                "comment": self.parse_html(),
            }

    def after_insert(self):
        self.notify_via_email()
        self.notify_via_push()

    def notify_via_email(self):
        if self.notification_type != "Mention":
            return

        if frappe.db.get_single_value("HD Settings", "skip_email_workflow"):
            return

        frappe.sendmail(
            recipients=self.user_to,
            subject="New notification",
            message=self.format_message(),
            template="notification",
            args=self.get_args(),
        )

    def notify_via_push(self):
        if not self.should_push():
            return

        # Browser push cue so the agent is alerted even when Helpdesk is not focused.
        frappe.publish_realtime(
            "helpdesk:new-notification",
            message={
                "notification_type": self.notification_type,
                "user_from": self.get_from() or self.user_from,
                "reference_ticket": self.reference_ticket,
            },
            user=self.user_to,
            after_commit=True,
        )

    def should_push(self):
        if self.notification_type in ("Assignment", "Mention"):
            return True
        # "Reaction" covers both comment emoji-reactions and ticket reopens.
        # Only a reopen (no linked comment) is worth a push.
        return self.notification_type == "Reaction" and not self.reference_comment
