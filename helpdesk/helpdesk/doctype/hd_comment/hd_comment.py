# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_user_info_for_avatar

from helpdesk.mixins.mentions import HasMentions
from helpdesk.utils import is_agent, refetch_resource


class HDComment(HasMentions, Document):
	mentions_field = "content"

	def get_list_filters(query):
		Comment = frappe.qb.DocType("HD Comment")
		if not is_agent():
			query = query.where(Comment.comment_type == "Public")
		return query

	def as_dict(self, *args, **kwargs):
		d = super(HDComment, self).as_dict(*args, **kwargs)
		d.user = get_user_info_for_avatar(d.user)
		return d

	def before_validate(self):
		self.user = frappe.session.user
		self.strip_recipients()
		self.fetch_attachments()

	def fetch_attachments(self):
		"""
		Fetch attachments from `File` doctype.
		"""
		for i in self.attachments:
			if isinstance(i, str):
				continue
			f = frappe.get_doc(
				"File",
				{
					# "attached_to_doctype": "HD Comment",
					"file_url": i.file_url,
				},
			).get("name")
			i.file = f

	def strip_recipients(self):
		"""
		Remove mail recipients if not needed
		"""
		if self.should_send_mail:
			return
		self.mail_to = None
		self.mail_cc = None
		self.mail_bcc = None

	def validate(self):
		self.validate_private()

	def validate_private(self):
		"""
		`Private` comments can be added by agents only.
		"""
		if self.comment_type == "Private" and not is_agent():
			err = _("Only agents can create private comments")
			frappe.throw(err, frappe.PermissionError)

	def after_insert(self):
		refetch_resource(self.cache_many)
		self.send_mail()

	def on_trash(self):
		refetch_resource(self.cache_many)

	@property
	def cache_many(self):
		return ["Comments", self.name]

	@property
	def parent(self):
		"""
		Fetch parent. For example, if this comment is attached to a ticket, then
		a ticket doc is returned

		:return: Parent document
		"""
		return frappe.get_doc(self.reference_doctype, self.reference_name)

	def send_mail(self):
		"""
		Send an email with content of this comment. Also, create a communication.
		`reference_doctype` and `reference_name` can be used to do this without
		manually creating a communication. This also helps with unwanted ignore
		permissions.
		"""
		if not self.should_send_mail:
			return
		frappe.sendmail(
			# sender
			add_unsubscribe_link=0,
			bcc=self.mail_bcc,
			cc=self.mail_cc,
			content=self.content,
			delayed=0,
			recipients=self.mail_to,
			reference_doctype=self.reference_doctype,
			reference_name=self.reference_name,
			send_priority=2,
			subject=self.parent.subject,
		)
