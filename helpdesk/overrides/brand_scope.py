import frappe

PRODUCT_BRANDS = ("Admin Central", "F360", "P360")


def permission_query(user=None):
    """Brand dropdowns show only the three product brands, except for administrators."""
    user = user or frappe.session.user
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return ""
    names = ", ".join(frappe.db.escape(b) for b in PRODUCT_BRANDS)
    return f"`tabHD Brand`.name in ({names})"
