from frappe.model.utils.rename_field import rename_field


def execute():
    """`enable` -> `enabled`, matching HD Ticket Status and the framework itself.

    A no-op on sites installed after the rename: rename_field bails out when the
    old column is gone.
    """
    rename_field("HD Agent Status", "enable", "enabled")
