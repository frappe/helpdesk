from frappe.utils import get_system_timezone


def get_boot() -> dict:
    """`window.boot` for the portal, there before its first date renders."""
    return {"system_timezone": get_system_timezone()}
