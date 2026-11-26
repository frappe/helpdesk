import frappe


def execute():
    """Sites with more than the welcome ticket every install ships skip the first-run setup.
    A site with only that ticket, like a v2 site created but not yet used, still gets it.
    """
    if frappe.db.count("HD Ticket") > 1:
        frappe.db.set_single_value("HD Settings", "setup_complete", 1)
