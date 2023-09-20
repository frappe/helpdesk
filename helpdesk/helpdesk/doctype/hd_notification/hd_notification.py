import frappe
from frappe.model.document import Document

from helpdesk.utils import refetch_resource


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

	def get_args(self):
		if self.notification_type == "Mention":
			return {
				"title": self.format_message(),
				"button_label": self.get_button_label(),
				"callback_url": self.get_url(),
			}

	def after_insert(self):
		frappe.sendmail(
			recipients=self.user_to,
			subject="New notification",
			message=self.format_message(),
			template="notification",
			args=self.get_args(),
		)

	def on_update(self):
		refetch_resource("Notifications")
