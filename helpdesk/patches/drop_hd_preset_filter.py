import frappe


def execute():
    # remove all records from Doctpe "HD Preset Filter" & "HD Preset Filter Item"
    frappe.delete_doc("DocType", "HD Preset Filter", force=True)
    print("Dropping table HD Preset Filter ")

    frappe.delete_doc("DocType", "HD Preset Filter Item", force=True)
    print("Dropping table HD Preset Filter Item ")
    # remove all references to HD Preset Filter & HD Preset Filter Item in other doctypes
    # drop table
    frappe.db.sql(
        """
		DROP TABLE IF EXISTS `tabHD Preset Filter`;
		DROP TABLE IF EXISTS `tabHD Preset Filter Item`;
	"""
    )

    pass


#
