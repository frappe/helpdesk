import frappe


doctype_map = {
	"Agent Group Item": "HD Team Item",
	"Agent Group": "HD Team",
	"Agent": "HD Agent",
	"Article Item": "HD Article Item",
	"Article": "HD Article",
	"Canned Response": "HD Canned Response",
	"Category": "HD Article Category",
	"Desk Account Request": "HD Desk Account Request",
	"FD Customer": "HD Customer",
	"FD Preset Filter Item": "HD Preset Filter Item",
	"FD Preset Filter": "HD Preset Filter",
	"Frappe Desk Comment": "HD Ticket Comment",
	"Frappe Desk Notification": "HD Notification",
	"Frappe Desk Settings": "HD Settings",
	"Holiday": "HD Holiday",
	"Organization Contact Item": "HD Organization Contact Item",
	"Organization": "HD Organization",
	"Pause SLA On Status": "HD Pause Service Level Agreement On Status",
	"Portal Signup Request": "HD Portal Signup Request",
	"SLA Fulfilled On Status": "HD Service Level Agreement Fulfilled On Status",
	"SLA": "HD Service Level Agreement",
	"Service Day": "HD Service Day",
	"Service Holiday List": "HD Service Holiday List",
	"Service Level Priority": "HD Service Level Priority",
	"Sub Category Item": "HD Article Sub Category Item",
	"Support Search Source": "HD Support Search Source",
	"Teams User": "HD Team Member",
	"Ticket Activity": "HD Ticket Activity",
	"Ticket Custom Field Item": "HD Ticket Custom Field Item",
	"Ticket Custom Field": "HD Ticket Custom Field",
	"Ticket Custom Fields Config": "HD Ticket Custom Field Config",
	"Ticket Priority": "HD Ticket Priority",
	"Ticket Template DocField": "HD Ticket Template DocField",
	"Ticket Template": "HD Ticket Template",
	"Ticket Type": "HD Ticket Type",
	"Ticket": "HD Ticket",
	"User Article Feedback": "HD Article Feedback",
}


def execute():
	for doctype in doctype_map:
		old = doctype
		new = doctype_map[doctype]

		if frappe.db.exists("DocType", new):
			continue

		if not frappe.db.exists("DocType", old):
			continue

		frappe.rename_doc("DocType", old, new)
		print("Migrated", old, "to", new)
