import frappe
from frappe.model.document import Document
from frappe.utils import random_string, get_url


class HDDeskAccountRequest(Document):
	def before_save(self):
		if not self.request_key:
			self.request_key = random_string(32)

		self.ip_address = frappe.local.request_ip

	def after_insert(self):
		self.send_verification_email()

	def send_verification_email(self):
		url = get_url(f"/helpdesk/verify/{self.request_key}")
		subject = "Verify your account"
		sender = None

		if frappe.db.exists(
			"Email Account", {"name": "Support", "enable_outgoing": True}
		):
			sender = frappe.get_doc("Email Account", "Support").email_id

		try:
			frappe.sendmail(
				recipients=self.email,
				sender=sender,
				subject=subject,
				template="email_verification",
				args=dict(link=url),
				now=True,
			)
		except Exception:
			frappe.throw(
				"Either setup up Support email account or there should be a default"
				" outgoing email account"
			)
