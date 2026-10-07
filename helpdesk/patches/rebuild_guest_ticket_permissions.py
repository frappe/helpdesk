import frappe


def execute():
    """Rebuild the Guest rules on HD Ticket from `allow_anyone_to_create_tickets`.

    Guest held `if_owner` read and write, which exposed every guest ticket to every
    visitor because all of them are owned by "Guest", and each settings save stacked
    another copy of that rule.
    """
    frappe.get_single("HD Settings").update_ticket_permissions()
