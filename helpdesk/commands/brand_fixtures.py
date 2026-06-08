import click
import frappe
from frappe.commands import pass_context


@click.command("setup-brand-fixtures")
@pass_context
def setup_brand_fixtures(context):
	"""Create default HD Brand records for multi-tenant testing"""
	site = context.sites[0] if context.sites else None

	if not site:
		click.echo("Error: No site specified")
		return

	frappe.init(site=site)
	frappe.connect()

	try:
		from helpdesk.fixtures.hd_brand_records import create_brand_records
		create_brand_records()
		click.echo("✓ Brand fixtures created successfully")
	except Exception as e:
		click.echo(f"✗ Error creating brand fixtures: {str(e)}")
		frappe.log_error(f"Brand fixture creation failed: {str(e)}")
	finally:
		frappe.destroy()


@click.command("remove-brand-fixtures")
@pass_context
def remove_brand_fixtures(context):
	"""Remove default HD Brand fixture records"""
	site = context.sites[0] if context.sites else None

	if not site:
		click.echo("Error: No site specified")
		return

	frappe.init(site=site)
	frappe.connect()

	try:
		from helpdesk.fixtures.hd_brand_records import delete_brand_records
		delete_brand_records()
		click.echo("✓ Brand fixtures removed successfully")
	except Exception as e:
		click.echo(f"✗ Error removing brand fixtures: {str(e)}")
		frappe.log_error(f"Brand fixture removal failed: {str(e)}")
	finally:
		frappe.destroy()


commands = [
	setup_brand_fixtures,
	remove_brand_fixtures,
]
