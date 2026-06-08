"""
HD Brand Fixture Records - Multi-Tenant Setup
Sprint 5: Brand records for Tiberbu and DHA tenants
"""

import frappe
from frappe import _


def create_brand_records():
	"""
	Create default HD Brand records for multi-tenant configuration
	Safe to run multiple times (checks for existing records)
	"""
	brands = [
		{
			"name": "tiberbu",
			"brand_name": "Tiberbu Support",
			"is_active": 1,
			"is_default": 1,
			"portal_domain": "support.tiberbu.app",
			"logo": "",  # Can be set via UI
			"wordmark": "",
			"favicon": "",
			"bg_image": "",
			"primary_color": "#059669",  # Emerald green
			"accent_color": "#047857",
			"bg_tint_color": "rgba(5, 150, 105, 0.08)",
			"headline": _("Welcome to Tiberbu Support"),
			"supporting_copy": _("Get help with your tickets, browse our knowledge base, and connect with our team."),
			"support_email": "support@tiberbu.app",
			"perks": [
				{
					"label": _("Fast Response"),
					"description": _("Our team responds within 2 hours during business days")
				},
				{
					"label": _("Expert Support"),
					"description": _("Dedicated support specialists for your needs")
				},
				{
					"label": _("Knowledge Base"),
					"description": _("Comprehensive guides and documentation")
				}
			],
			"trust_stats": [
				{"value": "500+", "label": _("Happy Clients")},
				{"value": "99%", "label": _("Satisfaction")},
				{"value": "<2h", "label": _("Response Time")}
			]
		},
		{
			"name": "dha",
			"brand_name": "DHA Helpdesk",
			"is_active": 1,
			"is_default": 0,
			"portal_domain": "support.dha.example",  # Update with actual domain
			"logo": "",
			"wordmark": "",
			"favicon": "",
			"bg_image": "",
			"primary_color": "#0891B2",  # Teal
			"accent_color": "#0E7490",
			"bg_tint_color": "rgba(8, 145, 178, 0.08)",
			"headline": _("Welcome to DHA Support Portal"),
			"supporting_copy": _("Professional healthcare support at your fingertips. Track tickets and access resources 24/7."),
			"support_email": "support@dha.example",
			"perks": [
				{
					"label": _("24/7 Access"),
					"description": _("Submit and track tickets any time, day or night")
				},
				{
					"label": _("Secure & Private"),
					"description": _("HIPAA-compliant ticket handling and data protection")
				},
				{
					"label": _("Medical Expertise"),
					"description": _("Specialized support for healthcare IT systems")
				}
			],
			"trust_stats": [
				{"value": "10k+", "label": _("Healthcare Users")},
				{"value": "99.9%", "label": _("Uptime SLA")},
				{"value": "24/7", "label": _("Availability")}
			]
		}
	]

	for brand_data in brands:
		# Check if brand already exists
		if frappe.db.exists("HD Brand", brand_data["name"]):
			frappe.msgprint(_("Brand {0} already exists. Skipping.").format(brand_data["name"]))
			continue

		# Create HD Brand document
		brand_doc = frappe.new_doc("HD Brand")
		brand_doc.update({
			"name": brand_data["name"],
			"brand_name": brand_data["brand_name"],
			"is_active": brand_data["is_active"],
			"is_default": brand_data.get("is_default", 0),
			"portal_domain": brand_data["portal_domain"],
			"logo": brand_data.get("logo", ""),
			"wordmark": brand_data.get("wordmark", ""),
			"favicon": brand_data.get("favicon", ""),
			"bg_image": brand_data.get("bg_image", ""),
			"primary_color": brand_data["primary_color"],
			"accent_color": brand_data["accent_color"],
			"bg_tint_color": brand_data["bg_tint_color"],
			"headline": brand_data["headline"],
			"supporting_copy": brand_data["supporting_copy"],
			"support_email": brand_data["support_email"],
		})

		# Add perks as child table entries
		for perk in brand_data.get("perks", []):
			brand_doc.append("perks", {
				"label": perk["label"],
				"description": perk["description"]
			})

		# Add trust stats as child table entries
		for stat in brand_data.get("trust_stats", []):
			brand_doc.append("trust_stats", {
				"value": stat["value"],
				"label": stat["label"]
			})

		try:
			brand_doc.insert(ignore_permissions=True)
			frappe.msgprint(_("Created brand: {0}").format(brand_data["name"]))
		except Exception as e:
			frappe.log_error(f"Failed to create brand {brand_data['name']}: {str(e)}")
			frappe.msgprint(_("Error creating brand {0}: {1}").format(brand_data["name"], str(e)))

	frappe.db.commit()
	frappe.msgprint(_("Brand setup complete!"))


def delete_brand_records():
	"""
	Remove fixture brand records (for cleanup/testing)
	"""
	brand_names = ["tiberbu", "dha"]

	for brand_name in brand_names:
		if frappe.db.exists("HD Brand", brand_name):
			frappe.delete_doc("HD Brand", brand_name, ignore_permissions=True, force=True)
			frappe.msgprint(_("Deleted brand: {0}").format(brand_name))

	frappe.db.commit()
	frappe.msgprint(_("Brand cleanup complete!"))
