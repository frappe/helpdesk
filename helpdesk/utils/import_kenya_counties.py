# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _


def import_counties_and_subcounties():
	"""Import all Kenya counties and subcounties from JSON data"""

	# Load the JSON data
	with open('/tmp/kenya-data/counties.json', 'r') as f:
		counties_data = json.load(f)

	print(f"Found {len(counties_data)} counties to import...")

	counties_created = 0
	subcounties_created = 0
	counties_skipped = 0
	subcounties_skipped = 0

	for county_data in counties_data:
		county_name = county_data['name']
		county_code = county_data.get('code')
		capital = county_data.get('capital', '')

		# Check if county already exists
		if frappe.db.exists('HD County', county_name):
			counties_skipped += 1
			county_exists = True
		else:
			# Create county
			try:
				county_doc = frappe.get_doc({
					'doctype': 'HD County',
					'county_name': county_name,
					'county_code': county_code,
					'capital': capital
				})
				county_doc.insert(ignore_permissions=True)
				print(f"  ✅ Created county: {county_name} (Code: {county_code})")
				counties_created += 1
				county_exists = True
			except Exception as e:
				print(f"  ❌ Error creating county {county_name}: {str(e)}")
				county_exists = False

		if not county_exists:
			continue

		# Import subcounties for this county
		sub_counties = county_data.get('sub_counties', [])
		sc_count = 0

		for subcounty_name in sub_counties:
			if not subcounty_name or subcounty_name.strip() == '':
				continue

			subcounty_name = subcounty_name.strip()

			# Check if subcounty already exists
			existing = frappe.db.get_value('HD Subcounty',
											{'subcounty_name': subcounty_name, 'county': county_name},
											'name')

			if existing:
				subcounties_skipped += 1
				continue

			# Create subcounty
			try:
				subcounty_doc = frappe.get_doc({
					'doctype': 'HD Subcounty',
					'subcounty_name': subcounty_name,
					'county': county_name
				})
				subcounty_doc.insert(ignore_permissions=True)
				subcounties_created += 1
				sc_count += 1
			except Exception as e:
				print(f"    ❌ Error creating subcounty {subcounty_name}: {str(e)}")

		if sc_count > 0:
			print(f"    📍 Created {sc_count} new subcounties for {county_name}")

	# Commit all changes
	frappe.db.commit()

	# Print summary
	print("\n" + "="*60)
	print("✅ IMPORT COMPLETE!")
	print("="*60)
	print(f"Counties:")
	print(f"  • Created: {counties_created}")
	print(f"  • Skipped (already exist): {counties_skipped}")
	print(f"\nSubcounties:")
	print(f"  • Created: {subcounties_created}")
	print(f"  • Skipped (already exist): {subcounties_skipped}")
	print(f"\nTotal:")
	print(f"  • {counties_created + counties_skipped} counties in database")
	print(f"  • {subcounties_created + subcounties_skipped} subcounties in database")
	print("="*60)
