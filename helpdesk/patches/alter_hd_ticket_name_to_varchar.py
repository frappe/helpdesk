import frappe
from frappe import _


def execute():
    alter_new_column()
    drop_autoincrement_sequence()


def get_current_column_type():
    result = frappe.db.sql(
        """
        SELECT DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'tabHD Ticket'
        AND COLUMN_NAME = 'name'
        """,
        as_dict=True,
    )
    return result[0]["DATA_TYPE"].lower() if result else None


def alter_new_column():
    current_type = get_current_column_type()

    if current_type is None:
        frappe.throw(_("Cou`ld not find the `name` column in tabHD Ticket"))

    if current_type == "varchar":
        print("alter_hd_ticket_name_to_varchar: column is already VARCHAR, skipping")
        return

    frappe.db.sql_ddl(
        "ALTER TABLE `tabHD Ticket` MODIFY COLUMN `name` VARCHAR(140) NOT NULL"
    )

    print(
        f"alter_hd_ticket_name_to_varchar: changed `name` from {current_type} to VARCHAR(140)"
    )


def drop_autoincrement_sequence():
    seq_name = frappe.scrub("HD Ticket") + "_id_seq"
    frappe.db.sql_ddl(f"DROP SEQUENCE IF EXISTS `{seq_name}`")
    print(
        f"alter_hd_ticket_name_to_varchar: dropped sequence `{seq_name}` if it existed."
    )
