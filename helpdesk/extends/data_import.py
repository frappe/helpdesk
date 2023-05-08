import frappe

from frappe.handler import upload_file
from frappe.model.document import Document


@frappe.whitelist()
def bulk_insert(
	target_doctype: str, import_type: str = "Insert New Records"
) -> Document:
	"""
	Upload a file and initiate an import against a DocType. File can be of any
	type supported by data import tool. File should be in a form with key `file`.

	Caveats
	- `doctype` can not be used as argument, since it is already used by `upload_file`
	- `file` is not an explicit argument, but is required by `upload_file`

	:param target_doctype: DocType against which import should be performed
	:param import_type: An import type supported by data import tool
	:return: Newly created `Data Import` document
	"""
	file = upload_file()
	data_import_doc = frappe.get_doc(
		{
			"doctype": "Data Import",
			"reference_doctype": target_doctype,
			"import_type": import_type,
			"import_file": file.file_url,
		}
	)

	data_import_doc.save()
	data_import_doc.start_import()

	return data_import_doc
