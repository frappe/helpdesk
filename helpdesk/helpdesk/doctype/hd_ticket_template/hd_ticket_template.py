# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.website.utils import cleanup_page_name


class HDTicketTemplate(Document):
	def validate(self):
		allowed_field_types = [
			"Link",
			"Select",
		]

		for field in self.fields:
			if field.fieldtype not in allowed_field_types:
				frappe.throw(
					f"Type {field.fieldtype} not allowed, should be in {allowed_field_types}"
				)
			if not field.fieldname:
				field.fieldname = cleanup_page_name(field.label)

			if field.fieldname == "description" and field.fieldtype != "Text Editor":
				frappe.throw(f"field type for description field should be Text Editor")

	def before_save(self):
		self.template_route = cleanup_page_name(self.template_name)

	def on_change(self):
		refresh_server_script()


def refresh_server_script():
	all_hd_ticket_templates = frappe.get_all("HD Ticket Template")

	snippets = []

	snippets.append("temp_custom_fields=doc.custom_fields")
	snippets.append("custom_fields={}")
	snippets.append("for f in temp_custom_fields:")
	snippets.append("\tcustom_fields[f.fieldname]=f.value")

	for template in all_hd_ticket_templates:
		template_doc = frappe.get_doc("HD Ticket Template", template)
		flag = False
		for field in template_doc.fields:
			if field.auto_set and field.auto_set_via == "Backend (Python)":
				if not flag:
					snippets.append(f"if doc.template == '{template.name}':")
					flag = True

				route = ""
				if field.fieldtype == "Link":
					route = f'"/app/{cleanup_page_name(field.options)}/" + {field.value_backend}'
				elif field.fieldtype == "Custom Link":
					route = field.value_backend
				snippets.append(
					"\tdoc.append('custom_fields', {'label': '%s', 'fieldname': '%s',"
					" 'value': %s, 'route': %s, 'is_action_field': %s})"
					% (
						field.label,
						field.fieldname,
						f"{field.value_backend}",
						route,
						field.is_action_field,
					)
				)

	server_script = frappe.get_doc("Server Script", "Ticket Auto Set Custom Fields")
	server_script.script = "\n".join(snippets) if len(snippets) > 0 else "# Do Nothing"
	server_script.save()
