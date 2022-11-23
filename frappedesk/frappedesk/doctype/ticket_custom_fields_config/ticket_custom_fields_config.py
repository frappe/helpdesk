# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


class TicketCustomFieldsConfig(Document):
	pass
