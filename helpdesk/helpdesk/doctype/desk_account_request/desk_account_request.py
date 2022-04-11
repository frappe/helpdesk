# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import random_string, get_url

class DeskAccountRequest(Document):
	def before_save(self):
		if not self.request_key:
			self.request_key = random_string(32)

		self.ip_address = frappe.local.request_ip
	
	def after_insert(self):
		self.send_verification_email()

	def send_verification_email(self):
		url = get_url(f"/support/verify/{self.request_key}")

		subject = "Verify your account"

		frappe.sendmail(
			recipients=self.email,
			subject=subject,
			template="email_verification",
			args=dict(
				link=url
			),
			now=True,
		)