# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FrappeDeskNotification(Document):
	def after_insert(self):
		frappe.publish_realtime("frappedesk:new_notification", user=self.to_user)