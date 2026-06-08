import frappe
import json
import os

def install_canned_responses():
    """Install default canned responses from fixtures"""
    fixture_path = os.path.join(
        frappe.get_app_path('helpdesk'),
        'fixtures',
        'hd_canned_response.json'
    )

    with open(fixture_path, 'r') as f:
        fixtures = json.load(f)

    for fixture in fixtures:
        existing = frappe.db.exists('HD Canned Response', fixture.get('title'))
        if not existing:
            doc = frappe.get_doc(fixture)
            doc.insert(ignore_permissions=True)
            frappe.logger().info(f"Created canned response: {fixture.get('title')}")

    frappe.db.commit()
