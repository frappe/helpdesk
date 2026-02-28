import frappe


def get_site_info(site_info):
    # called via hook
    return {"activation": get_sales_data(site_info)}


def get_sales_data(site_info):
    activation_level = site_info.get("activation", {}).get("activation_level", 0)
    sales_data = site_info.get("activation", {}).get("sales_data", [])
    doctypes = [
        "HD Ticket",
        "HD Ticket Comment",
        "Communication",
        "HD Saved Reply",
        "HD Service Level Agreement",
        "HD Form Script",
        "HD Article",
        "HD Customer",
        "HD Team",
    ]

    for doctype in doctypes:
        count = frappe.db.count(doctype)
        sales_data.append({doctype: count})

    return {"activation_level": activation_level, "sales_data": sales_data}
