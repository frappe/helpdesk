import frappe 
from frappe import _

def execute():
    
    alter_hd_ticket_name_column()
    
    max_id = get_largest_hd_ticket_id()
    
    if not max_id:
        return
    
    update_series_counter(max_id)
    
    frappe.db.commit()
    
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


def alter_hd_ticket_name_column():
    current_type = get_current_column_type()

    if current_type is None:
        frappe.throw(_("Could not find the `name` column in tabHD Ticket"))

    if current_type == "varchar":
        print("alter_hd_ticket_name_to_varchar: column is already VARCHAR, skipping")
        return

    frappe.db.sql_ddl(
        "ALTER TABLE `tabHD Ticket` MODIFY COLUMN `name` VARCHAR(140) NOT NULL"
    )

    print(
        f"alter_hd_ticket_name_to_varchar: changed `name` from {current_type} to VARCHAR(140)"
    )
    
def get_largest_hd_ticket_id():
        result = frappe.db.sql("""
                               SELECT MAX(CAST(name as UNSIGNED))
                               FROM `tabHD Ticket`
                               """)
        
        return result[0][0] if result else 0
    
def update_series_counter(max_id):
        series_name = ""
        existing_counter_val = frappe.db.sql("SELECT current FROM `tabSeries` WHERE name=%s", (series_name,))
        current_counter_val = existing_counter_val[0][0] if existing_counter_val else None
        
        if current_counter_val is None:
            frappe.db.sql("INSERT INTO `tabSeries` (name, current) VALUES (%s, %s)",
            (series_name,max_id))
            
        elif max_id>current_counter_val:
            frappe.db.sql(
            "UPDATE `tabSeries` SET current=%s WHERE name=%s", 
            (max_id, series_name)
        )
    
    