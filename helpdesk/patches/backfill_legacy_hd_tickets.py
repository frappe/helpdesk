import frappe
from frappe.utils import getdate


def execute():
    migrate_ticket_names()
    seed_series


def migrate_ticket_names():
    legacy_tickets = frappe.db.sql(
        """
        SELECT name, creation 
        FROM `tabHD Ticket` 
        WHERE name NOT LIKE 'HD-TKT-%'
        ORDER BY CAST(name AS UNSIGNED) ASC
    """,
        as_dict=True,
    )

    if legacy_tickets:
        for index, ticket in enumerate(legacy_tickets):
            old_name = ticket.name
            try:
                old_id = int(old_name)
                year = getdate(ticket.creation).year
                new_name = f"HD-TKT-{year}-{old_id:05d}"

                frappe.rename_doc("HD Ticket", old_name, new_name, force=True)
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(), f"Failed to migrate HD Ticket {old_name}"
                )
                continue

            if (index + 1) % 500 == 0:
                frappe.db.commit()

        frappe.db.commit()


def seed_series():
    # Extract year and sequence from names like:
    # HD-TKT-2026-00001
    yearly_max_data = frappe.db.sql(
        """
        SELECT 
            SUBSTRING(name, 8, 4) as year, 
            MAX(CAST(RIGHT(name, 5) AS UNSIGNED)) as max_id
        FROM `tabHD Ticket`
        WHERE name LIKE 'HD-TKT-____-_____'
        GROUP BY year
    """,
        as_dict=True,
    )

    if yearly_max_data:
        for data in yearly_max_data:
            year = data.year
            max_id = data.max_id
            series_name = f"HD-TKT-{year}-"

            res = frappe.db.sql(
                "SELECT current FROM `tabSeries` WHERE name=%s", (series_name,)
            )
            current_val = res[0][0] if res else None

            if current_val is None:
                frappe.db.sql(
                    "INSERT INTO `tabSeries` (name, current) VALUES (%s, %s)",
                    (series_name, max_id),
                )
            elif max_id > current_val:
                frappe.db.sql(
                    "UPDATE `tabSeries` SET current = %s WHERE name = %s",
                    (max_id, series_name),
                )

    frappe.db.commit()
