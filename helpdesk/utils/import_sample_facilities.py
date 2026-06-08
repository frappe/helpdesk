# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def import_sample_facilities():
	"""Import sample healthcare facilities for testing"""

	sample_facilities = [
		# Nairobi facilities
		{
			'facility_name': 'Kenyatta National Hospital',
			'facility_code': 'KNH-001',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Nairobi',
			'subcounty': 'Nairobi',  # Will be set to proper Link name
			'ward': 'Kilimani',
			'phone_number': '0202726300',
			'email': 'info@knh.or.ke',
			'bed_capacity': 1800,
			'services_offered': 'General Medicine, Surgery, Pediatrics, Maternity, ICU, Laboratory, Radiology',
			'gps_coordinates': '-1.3006, 36.8071'
		},
		{
			'facility_name': 'Nairobi Hospital',
			'facility_code': 'NH-002',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Private',
			'county': 'Nairobi',
			'subcounty': 'Nairobi',
			'ward': 'Parklands',
			'phone_number': '0202845000',
			'email': 'info@nbihosp.org',
			'bed_capacity': 200,
			'services_offered': 'General Medicine, Surgery, Maternity, Laboratory, Radiology, Pharmacy',
			'gps_coordinates': '-1.2685, 36.8076'
		},
		{
			'facility_name': 'Mama Lucy Kibaki Hospital',
			'facility_code': 'MLK-003',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Nairobi',
			'subcounty': 'Nairobi',
			'ward': 'Embakasi',
			'phone_number': '0709292000',
			'email': 'info@mamalucy.go.ke',
			'bed_capacity': 200,
			'services_offered': 'General Medicine, Maternity, Pediatrics, Laboratory',
			'gps_coordinates': '-1.2987, 36.9170'
		},
		# Mombasa facilities
		{
			'facility_name': 'Coast General Teaching and Referral Hospital',
			'facility_code': 'CGTRH-004',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Mombasa',
			'subcounty': 'Mombasa',
			'ward': 'Tononoka',
			'phone_number': '0412313440',
			'email': 'info@coasthospital.go.ke',
			'bed_capacity': 650,
			'services_offered': 'General Medicine, Surgery, Maternity, Pediatrics, ICU, Laboratory, Radiology',
			'gps_coordinates': '-4.0548, 39.6705'
		},
		{
			'facility_name': 'Aga Khan Hospital Mombasa',
			'facility_code': 'AKHM-005',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Private',
			'county': 'Mombasa',
			'subcounty': 'Mombasa',
			'ward': 'Nyali',
			'phone_number': '0412222710',
			'email': 'mombasa@akhms.co.ke',
			'bed_capacity': 90,
			'services_offered': 'General Medicine, Surgery, Maternity, Laboratory, Radiology, Pharmacy',
			'gps_coordinates': '-4.0345, 39.7207'
		},
		# Nakuru facilities
		{
			'facility_name': 'Nakuru Provincial General Hospital',
			'facility_code': 'NPGH-006',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Nakuru',
			'subcounty': 'Nakuru',
			'ward': 'Nakuru East',
			'phone_number': '0512212273',
			'email': 'info@nakuruhospital.go.ke',
			'bed_capacity': 400,
			'services_offered': 'General Medicine, Surgery, Maternity, Pediatrics, Laboratory',
			'gps_coordinates': '-0.2932, 36.0819'
		},
		# Kiambu facilities
		{
			'facility_name': 'Thika Level 5 Hospital',
			'facility_code': 'TL5H-007',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Kiambu',
			'subcounty': 'Kiambu',
			'ward': 'Thika Town',
			'phone_number': '0202034000',
			'email': 'info@thikahospital.go.ke',
			'bed_capacity': 300,
			'services_offered': 'General Medicine, Surgery, Maternity, Pediatrics, Laboratory, ICU',
			'gps_coordinates': '-1.0332, 37.0728'
		},
		{
			'facility_name': 'Kiambu Level 4 Hospital',
			'facility_code': 'KL4H-008',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Kiambu',
			'subcounty': 'Kiambu',
			'ward': 'Kiambu Town',
			'phone_number': '0202036000',
			'email': 'info@kiambuhospital.go.ke',
			'bed_capacity': 150,
			'services_offered': 'General Medicine, Maternity, Pediatrics, Laboratory',
			'gps_coordinates': '-1.1716, 36.8356'
		},
		# Health centres
		{
			'facility_name': 'Kangemi Health Centre',
			'facility_code': 'KHC-009',
			'facility_type': 'Health Centre',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Nairobi',
			'subcounty': 'Nairobi',
			'ward': 'Kangemi',
			'phone_number': '0722123456',
			'bed_capacity': 20,
			'services_offered': 'Outpatient, Maternity, Laboratory, Pharmacy',
			'gps_coordinates': '-1.2716, 36.7441'
		},
		{
			'facility_name': 'Likoni Sub-County Hospital',
			'facility_code': 'LSH-010',
			'facility_type': 'Hospital',
			'status': 'Active',
			'ownership': 'Government',
			'county': 'Mombasa',
			'subcounty': 'Mombasa',
			'ward': 'Likoni',
			'phone_number': '0722234567',
			'bed_capacity': 100,
			'services_offered': 'General Medicine, Maternity, Pediatrics, Laboratory',
			'gps_coordinates': '-4.0953, 39.6735'
		}
	]

	facilities_created = 0
	facilities_skipped = 0

	print(f"Importing {len(sample_facilities)} sample facilities...")

	for facility_data in sample_facilities:
		facility_name = facility_data['facility_name']
		county = facility_data['county']

		# Check if facility already exists
		if frappe.db.exists('HD Facility', facility_name):
			print(f"  ⏭️  Facility '{facility_name}' already exists")
			facilities_skipped += 1
			continue

		# Get a valid subcounty for this county
		subcounty = frappe.db.get_value('HD Subcounty', {'county': county}, 'name')
		if subcounty:
			facility_data['subcounty'] = subcounty
		else:
			print(f"  ⚠️  No subcounty found for {county}, skipping {facility_name}")
			continue

		# Create facility
		try:
			facility_doc = frappe.get_doc({
				'doctype': 'HD Facility',
				**facility_data
			})
			facility_doc.insert(ignore_permissions=True)
			print(f"  ✅ Created: {facility_name} ({county} - {subcounty})")
			facilities_created += 1
		except Exception as e:
			print(f"  ❌ Error creating {facility_name}: {str(e)}")

	# Commit all changes
	frappe.db.commit()

	# Print summary
	print("\n" + "="*60)
	print("✅ SAMPLE FACILITIES IMPORT COMPLETE!")
	print("="*60)
	print(f"Facilities:")
	print(f"  • Created: {facilities_created}")
	print(f"  • Skipped (already exist): {facilities_skipped}")
	print(f"\nTotal: {facilities_created + facilities_skipped} facilities in database")
	print("="*60)
