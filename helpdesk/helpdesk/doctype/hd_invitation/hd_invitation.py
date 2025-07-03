# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class HDInvitation(Document):
	def before_insert(self):
		frappe.utils.validate_email_address(self.email, True)
		self.key = frappe.generate_hash(length=12)
		self.invited_by = frappe.session.user
		self.status = "Pending"

	def after_insert(self):
		self.invite_via_email()

	def invite_via_email(self):
		invite_link = frappe.utils.get_url(f"/api/method/helpdesk.api.invitation_flow.accept_invitation?key={self.key}")
		if frappe.local.dev_server:
			print(f"Invite link for {self.email}: {invite_link}")
		title = "Frappe Helpdesk"
		template = "hd_invitation"
		frappe.sendmail(
			recipients=self.email,
			subject=f"You have been invited to join {title}",
			template=template,
			args={
				"title": title,
				"invite_link": invite_link,
				"invited_by": self.invited_by,
				"invited_as": self.role
			},
			now=True,
		)
		self.db_set("email_sent_at", frappe.utils.now())

	def accept(self):
		if self.status == "Expired":
			frappe.throw("Invalid or expired key")
		user = self.create_user_if_not_exists()
		if self.role == "Agent":
			user.append_roles("Agent")
		elif self.role == "Agent Manager":
			user.append_roles("Agent", "Agent Manager")
		elif self.role == "System Manager":
			user.append_roles("Agent", "Agent Manager", "System Manager")
		else:
			user.append_roles(self.role)
		if self.role == "Agent" or self.role == "Agent Manager":
			self.restrict_modules(user, "Helpdesk")
		user.save(ignore_permissions=True)
		create_agent_if_not_exists(user)
		self.status = "Accepted"
		self.accepted_at = frappe.utils.now()
		self.save(ignore_permissions=True)

	def restrict_modules(self, user, module):
		block_modules = frappe.get_all(
			"Module Def",
			fields=["name as module"],
			filters={"name": ["!=", module]},
		)
		if block_modules:
			user.set("block_modules", block_modules)

	def create_user_if_not_exists(self):
		if not frappe.db.exists("User", self.email):
			first_name = self.email.split("@")[0].title()
			user = frappe.get_doc(
				doctype="User",
				user_type="System User",
				email=self.email,
				send_welcome_email=0,
				first_name=first_name,
			).insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", self.email)
		return user

	def get_update_password_url(self):
		return password_link(frappe.get_doc("User", self.email))

def create_agent_if_not_exists(user):
	if not frappe.db.exists("HD Agent", {"user": user.email}):
		frappe.get_doc(
			doctype="HD Agent",
			user=user.email,
			agent_name=user.first_name,
			is_active=True
		).insert(ignore_permissions=True)

def password_link(user, password_expired=False):
	from frappe.utils import now_datetime, sha256_hash

	key = frappe.generate_hash()
	hashed_key = sha256_hash(key)
	user.reset_password_key = hashed_key
	user.last_reset_password_key_generated_on = now_datetime()
	user.save(ignore_permissions=True)
	frappe.db.commit()
	return f"/update-password?key={key}&redirect-to=/helpdesk{'&password_expired=true' if password_expired else ''}"
