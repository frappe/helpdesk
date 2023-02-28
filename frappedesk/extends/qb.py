import frappe

VERSION = frappe.__version__


def get_query(*args, **kwargs):
	if not VERSION.startswith("15"):
		return frappe.qb.engine.get_query(*args, **kwargs)

	return frappe.qb.get_query(*args, **kwargs)
