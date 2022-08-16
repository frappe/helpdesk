# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document


class FrappeDeskSettings(Document):
	def before_save(self):
		self.setup_complete = self.initial_agent_set and self.initial_demo_ticket_created
