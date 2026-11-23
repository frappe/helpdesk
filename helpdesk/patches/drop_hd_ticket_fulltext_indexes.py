from frappe.database.utils import drop_index_if_exists

FULLTEXT_INDEXES = ("ft_subject", "ft_description")


def execute() -> None:
    """Drop the unused FULLTEXT indexes on HD Ticket subject and description.
    Nothing queries them, and they slow every ticket write."""
    for index in FULLTEXT_INDEXES:
        drop_index_if_exists("tabHD Ticket", index)
