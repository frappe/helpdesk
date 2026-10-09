from frappe.model.utils.rename_field import rename_field


def execute():
    """Rename enable to enabled to match HD Ticket Status. Skips if the old
    column is already gone."""
    rename_field("HD Agent Status", "enable", "enabled")
