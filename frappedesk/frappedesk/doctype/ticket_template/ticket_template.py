# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.website.utils import cleanup_page_name
from frappe.utils.safe_exec import safe_exec

class TicketTemplate(Document):
	def validate(self):
		allowed_field_types = ['Data', 'Link', 'Long Text', 'Text Editor', 'Select']

		for field in self.fields:
			if field.fieldtype not in allowed_field_types:
				frappe.throw(f'Type {field.fieldtype} not allowed, should be in {allowed_field_types}')
			if not field.fieldname:
				field.fieldname = cleanup_page_name(field.label)
			if field.fieldname == 'description' and field.fieldtype != 'Text Editor':
				frappe.throw(f'field type for description field should be Text Editor')

		required_fields_not_added = []
		for fieldname in ['subject', 'description']:
			if not next((field for field in self.fields if field.fieldname == fieldname and field.reqd == True), None):
				required_fields_not_added.append(fieldname)

		if len(required_fields_not_added) > 0:
			frappe.throw(f'template mandetory fields {required_fields_not_added} are not added')


	def before_save(self):
		self.template_route = cleanup_page_name(self.template_name)

	def on_change(self):
		refresh_server_script()

def refresh_server_script():
	all_ticket_templates = frappe.get_all("Ticket Template")

	snippets = []
	for template in all_ticket_templates:
		template_doc = frappe.get_doc("Ticket Template", template)
		flag = False
		for field in template_doc.fields:
			if field.auto_set:
				if not flag:
					snippets.append(f"if doc.template == '{template.name}':")
					flag = True
				snippets.append("\tdoc.append('custom_fields', {'label': '%s', 'fieldname': '%s', 'value': %s, 'route': %s})" % (field.label, field.fieldname, f"{field.value}", f'"/app/{cleanup_page_name(field.options)}/" + {field.value}' if field.fieldtype == 'Link' else '""'))

	server_script = frappe.get_doc("Server Script", "Ticket Auto Set Custom Fields")
	server_script.script = '\n'.join(snippets) if len(snippets) > 0 else '# Do Nothing'
	server_script.save()

