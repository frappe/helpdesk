"""
Multi-Tenant Login Tests - Sprint 5
Tests for tenant override and brand resolution
"""

import frappe
from frappe.tests.utils import FrappeTestCase


class TestMultiTenantLogin(FrappeTestCase):
	"""Test suite for multi-tenant brand resolution"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Create test brand records
		cls.create_test_brands()

	@classmethod
	def tearDownClass(cls):
		# Clean up test brands
		cls.delete_test_brands()
		super().tearDownClass()

	@classmethod
	def create_test_brands(cls):
		"""Create test HD Brand records"""
		brands = [
			{
				"name": "test_tenant_a",
				"brand_name": "Test Tenant A",
				"is_active": 1,
				"is_default": 1,
				"portal_domain": "tenant-a.test.local",
				"primary_color": "#059669",
				"accent_color": "#047857",
				"bg_tint_color": "rgba(5, 150, 105, 0.08)",
				"headline": "Welcome to Tenant A",
				"supporting_copy": "Test tenant A support portal",
				"support_email": "support@tenant-a.test"
			},
			{
				"name": "test_tenant_b",
				"brand_name": "Test Tenant B",
				"is_active": 1,
				"is_default": 0,
				"portal_domain": "tenant-b.test.local",
				"primary_color": "#0891B2",
				"accent_color": "#0E7490",
				"bg_tint_color": "rgba(8, 145, 178, 0.08)",
				"headline": "Welcome to Tenant B",
				"supporting_copy": "Test tenant B support portal",
				"support_email": "support@tenant-b.test"
			}
		]

		for brand_data in brands:
			if not frappe.db.exists("HD Brand", brand_data["name"]):
				brand_doc = frappe.get_doc({
					"doctype": "HD Brand",
					**brand_data
				})
				brand_doc.insert(ignore_permissions=True)

		frappe.db.commit()

	@classmethod
	def delete_test_brands(cls):
		"""Remove test HD Brand records"""
		test_brands = ["test_tenant_a", "test_tenant_b"]
		for brand_name in test_brands:
			if frappe.db.exists("HD Brand", brand_name):
				frappe.delete_doc("HD Brand", brand_name, ignore_permissions=True, force=True)
		frappe.db.commit()

	def test_tenant_override_parameter(self):
		"""Test ?tenant=<slug> query parameter overrides host-based resolution"""
		from helpdesk.www.login_preview import resolve_brand

		# Mock frappe.form_dict to simulate query parameter
		original_form_dict = frappe.form_dict
		frappe.form_dict = frappe._dict({"tenant": "test_tenant_b"})

		try:
			brand = resolve_brand()
			self.assertEqual(brand["name"], "test_tenant_b")
			self.assertEqual(brand["display_name"], "Test Tenant B")
			self.assertEqual(brand["primary_color"], "#0891B2")
		finally:
			frappe.form_dict = original_form_dict

	def test_host_pattern_resolution(self):
		"""Test host-based brand resolution via portal_domain"""
		from helpdesk.www.login_preview import resolve_brand

		# Mock request host
		original_request = frappe.local.request
		frappe.local.request = frappe._dict({"host": "tenant-b.test.local"})

		# Clear form_dict to ensure no tenant override
		original_form_dict = frappe.form_dict
		frappe.form_dict = frappe._dict({})

		try:
			# Clear cache first
			cache_key = "hd_brand_by_host:tenant-b.test.local"
			frappe.cache().delete_value(cache_key)

			brand = resolve_brand()
			self.assertEqual(brand["name"], "test_tenant_b")
			self.assertEqual(brand["primary_color"], "#0891B2")
		finally:
			frappe.local.request = original_request
			frappe.form_dict = original_form_dict

	def test_default_brand_fallback(self):
		"""Test fallback to default brand when no match found"""
		from helpdesk.www.login_preview import resolve_brand

		# Mock unknown host
		original_request = frappe.local.request
		frappe.local.request = frappe._dict({"host": "unknown.test.local"})

		# Clear form_dict
		original_form_dict = frappe.form_dict
		frappe.form_dict = frappe._dict({})

		try:
			# Clear cache
			cache_key = "hd_brand_by_host:unknown.test.local"
			frappe.cache().delete_value(cache_key)

			brand = resolve_brand()
			# Should return default brand (test_tenant_a has is_default=1)
			self.assertEqual(brand["name"], "test_tenant_a")
		finally:
			frappe.local.request = original_request
			frappe.form_dict = original_form_dict

	def test_brand_enrichment(self):
		"""Test that brand data is enriched with computed fields"""
		from helpdesk.www.login_preview import _enrich_brand

		brand_doc = frappe._dict({
			"name": "test_enrichment",
			"brand_name": "Test",
			"primary_color": "#059669"
		})

		enriched = _enrich_brand(brand_doc)

		self.assertIn("accent_color", enriched)
		self.assertIn("bg_tint_color", enriched)
		self.assertIn("headline", enriched)
		self.assertIn("supporting_copy", enriched)
		self.assertIn("perks", enriched)
		self.assertIn("trust_stats", enriched)

	def test_cache_invalidation(self):
		"""Test that brand cache is invalidated on update"""
		from helpdesk.www.login_preview import resolve_brand, invalidate_brand_cache

		# Set up host
		original_request = frappe.local.request
		frappe.local.request = frappe._dict({"host": "tenant-a.test.local"})

		original_form_dict = frappe.form_dict
		frappe.form_dict = frappe._dict({})

		try:
			# First call - cache miss
			brand1 = resolve_brand()

			# Second call - cache hit
			brand2 = resolve_brand()
			self.assertEqual(brand1["name"], brand2["name"])

			# Invalidate cache
			invalidate_brand_cache()

			# Third call - cache miss after invalidation
			brand3 = resolve_brand()
			self.assertEqual(brand1["name"], brand3["name"])
		finally:
			frappe.local.request = original_request
			frappe.form_dict = original_form_dict

	def test_inactive_brand_not_resolved(self):
		"""Test that inactive brands are not returned"""
		# Deactivate test_tenant_b
		brand = frappe.get_doc("HD Brand", "test_tenant_b")
		brand.is_active = 0
		brand.save(ignore_permissions=True)
		frappe.db.commit()

		from helpdesk.www.login_preview import resolve_brand

		# Try to access via tenant override
		original_form_dict = frappe.form_dict
		frappe.form_dict = frappe._dict({"tenant": "test_tenant_b"})

		try:
			brand_result = resolve_brand()
			# Should NOT return test_tenant_b, should fallback
			self.assertNotEqual(brand_result["name"], "test_tenant_b")
		finally:
			frappe.form_dict = original_form_dict

			# Reactivate for cleanup
			brand.is_active = 1
			brand.save(ignore_permissions=True)
			frappe.db.commit()
