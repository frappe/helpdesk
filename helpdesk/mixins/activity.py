import frappe


class HasActivity:
	"""
	Mixin to add activity logging to a doctype. Target doctype must have `log_fields`
	property defined. This must be a `list` of fieldnames to log.
	"""

	def log_activity(self, custom_fields=False):
		doc_before = self.get_doc_before_save()
		if custom_fields:
			f = [f.fieldname for f in self.custom_fields]
			self.log_fields.extend(f)
		for f in self.log_fields:
			if self.has_value_changed(f):
				doc = {
					"doctype": "HD Activity",
					"reference_doctype": self.doctype,
					"reference_name": self.name,
					"user": frappe.session.user,
					"activity_type": "Value change",
					"value_change_field": self.doctype_fields.get(f).get("label"),
					"value_change_initial": doc_before.get(f),
					"value_change_final": self.get(f),
				}
				frappe.get_doc(doc).save()

	@property
	def doctype_fields(self) -> dict[str, any]:
		m = frappe.get_meta(self.doctype)
		r = {}
		for f in m.fields:
			r[f.fieldname] = f
		return r

	@property
	def custom_fields(self):
		r = []
		for f in self.doctype_fields:
			f = self.doctype_fields.get(f)
			is_custom = f.get("is_custom_field") == 1
			if is_custom:
				r.append(f)
		return r
