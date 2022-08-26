# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappedesk.utils import extract_mentions
from frappe.utils import get_fullname

class FrappeDeskComment(Document):
	def on_change(self):
		print(f'\n\nFrappe Desk Comment created : {self.name}\n\n')
		mentions = extract_mentions(self.content)
		print(f'\n\nMentions : {mentions}\n\n')
		for mention in mentions:
			values = frappe._dict(
				from_user=self.commented_by,
				to_user=mention.email,
				ticket=self.reference_ticket,
				comment=self.name
			)
			if frappe.db.exists("Frappe Desk Notification", values):
				continue
			notification = frappe.get_doc(doctype='Frappe Desk Notification')
			notification.message = f'{get_fullname(self.owner)} mentioned you in Ticket #{self.reference_ticket}',
			notification.update(values)
			notification.insert(ignore_permissions=True)
