import frappe
from frappe.utils import get_table_name

from helpdesk.utils import alphanumeric_to_int

DOCTYPE = "HD Ticket"
MODULE = "Helpdesk"
SEQ_SUFFIX = "_id_seq"


def execute():
	create_sequence()
	modify_table()


def modify_table():
	table = f"`{get_table_name(DOCTYPE)}`"
	frappe.db.sql_ddl(f"ALTER TABLE {table} MODIFY COLUMN name BIGINT(20)")
	frappe.reload_doc(MODULE, "DocType", DOCTYPE)


def create_sequence():
	sequence_name = frappe.scrub(DOCTYPE + SEQ_SUFFIX)
	frappe.db.sql_ddl(f"DROP SEQUENCE IF EXISTS {sequence_name}")
	start_value = sequence_start()
	frappe.db.create_sequence(DOCTYPE, check_not_exists=False, start_value=start_value)


def sequence_start():
	try:
		last_doc = frappe.get_last_doc(DOCTYPE)
		last_id = alphanumeric_to_int(last_doc.name) or 0
		return last_id + 1
	except:
		return 1
