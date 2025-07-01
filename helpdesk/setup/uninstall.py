import click
import frappe


def before_uninstall():
    remove_system_defaults()


def remove_system_defaults():
    click.secho("* Removing system defaults for HD Settings")
    fields = ["default_priority", "default_ticket_type", "base_support_rotation"]
    for field in fields:
        frappe.db.set_single_value("HD Settings", field, None)
