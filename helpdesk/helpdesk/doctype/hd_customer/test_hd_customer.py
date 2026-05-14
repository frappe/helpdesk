# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import (
    ERPNEXT_NOT_INSTALLED,
    make_erp_customer,
    make_hd_customer,
)


class TestHDCustomerSync(FrappeTestCase):
    """Integration tests for HD Customer ↔ ERPNext Customer bi-directional sync."""

    def tearDown(self):
        if "erpnext" in frappe.get_installed_apps():
            for erp_name in frappe.get_all(
                "Customer", {"customer_name": ("like", "Test%")}, pluck="name"
            ):
                linked_hd = frappe.db.get_value("Customer", erp_name, "hd_customer")
                if linked_hd and frappe.db.exists("HD Customer", linked_hd):
                    frappe.delete_doc(
                        "HD Customer", linked_hd, force=True, ignore_permissions=True
                    )
                frappe.delete_doc(
                    "Customer", erp_name, force=True, ignore_permissions=True
                )
        for hd_name in frappe.get_all(
            "HD Customer", {"name": ("like", "Test%")}, pluck="name"
        ):
            frappe.delete_doc(
                "HD Customer", hd_name, force=True, ignore_permissions=True
            )
        frappe.db.commit()  # nosemgrep

    # ------------------------------------------------------------------
    # Feature 1: HD Customer → ERPNext on insert
    # ------------------------------------------------------------------

    def test_hd_customer_insert_creates_erpnext_customer(self):
        """When ERPNext is installed, after_insert should create a linked ERPNext Customer."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        hd_doc = make_hd_customer("Test HD To ERP")
        hd_doc.reload()

        self.assertTrue(
            hd_doc.erpnext_customer, "erpnext_customer should be set after insert"
        )

        erp_name = hd_doc.erpnext_customer
        self.assertTrue(frappe.db.exists("Customer", erp_name))
        self.assertEqual(
            frappe.db.get_value("Customer", erp_name, "hd_customer"), hd_doc.name
        )

    @patch("frappe.get_installed_apps", return_value=ERPNEXT_NOT_INSTALLED)
    def test_hd_customer_insert_skips_sync_when_erpnext_not_installed(self, _mock):
        """When ERPNext is not installed, after_insert should be a no-op."""
        doc = make_hd_customer("Test No ERP Installed")
        self.assertFalse(doc.erpnext_customer)

    def test_hd_customer_sync_to_erpnext_skips_if_already_synced(self):
        """sync_to_erpnext should not create another ERPNext Customer if erpnext_customer is set."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        # Create a real linked pair manually
        erp_doc = make_erp_customer("Test Already Synced")
        hd_doc = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Already Synced"}
        )
        hd_doc.flags.ignore_erpnext_sync = True
        hd_doc.insert(ignore_permissions=True)
        hd_doc.db_set("erpnext_customer", erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)

        before = frappe.db.count(
            "Customer", {"customer_name": ("like", "Test Already Synced%")}
        )

        hd_doc.reload()
        hd_doc.sync_to_erpnext()

        after = frappe.db.count(
            "Customer", {"customer_name": ("like", "Test Already Synced%")}
        )
        self.assertEqual(
            before,
            after,
            "sync_to_erpnext must not create a duplicate ERPNext Customer",
        )

    def test_hd_customer_sync_to_erpnext_skips_when_loop_guard_set(self):
        """sync_to_erpnext should be a no-op when ignore_erpnext_sync is set."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        before = frappe.db.count("Customer")

        hd_doc = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Loop Guard"}
        )
        hd_doc.flags.ignore_erpnext_sync = True
        hd_doc.insert(ignore_permissions=True)

        after = frappe.db.count("Customer")
        self.assertEqual(
            before,
            after,
            "No ERPNext Customer should be created when loop guard is set",
        )

    # ------------------------------------------------------------------
    # Feature 2: ERPNext Customer → HD Customer on insert
    # ------------------------------------------------------------------

    def test_erp_customer_insert_creates_hd_customer(self):
        """Inserting an ERPNext Customer should create and link an HD Customer."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        erp_doc = make_erp_customer("Test ERP Creates HD", ignore_sync=False)

        hd_name = frappe.db.get_value("Customer", erp_doc.name, "hd_customer")
        self.assertTrue(
            hd_name, "hd_customer field on Customer should be set after insert"
        )
        self.assertTrue(frappe.db.exists("HD Customer", hd_name))
        self.assertEqual(
            frappe.db.get_value("HD Customer", hd_name, "erpnext_customer"),
            erp_doc.name,
        )

    def test_erp_customer_insert_links_existing_unlinked_hd_customer(self):
        """
        If an unlinked HD Customer with the same customer_name exists, after_insert should
        link it rather than creating a new one (step 1 of create_or_link_hd_customer).
        """
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        # Pre-create an unlinked HD Customer with the same customer_name
        hd_doc = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test ERP Link Existing"}
        )
        hd_doc.flags.ignore_erpnext_sync = True
        hd_doc.insert(ignore_permissions=True)
        self.assertFalse(hd_doc.erpnext_customer)

        # Insert ERPNext Customer with matching customer_name (no ignore_sync)
        erp_doc = make_erp_customer("Test ERP Link Existing", ignore_sync=False)

        # Step 1 of create_or_link_hd_customer should have claimed the pre-existing HD Customer
        linked_hd = frappe.db.get_value("Customer", erp_doc.name, "hd_customer")
        self.assertEqual(linked_hd, "Test ERP Link Existing")
        self.assertEqual(
            frappe.db.get_value(
                "HD Customer", "Test ERP Link Existing", "erpnext_customer"
            ),
            erp_doc.name,
        )

    def test_erp_customer_insert_skips_when_loop_guard_set(self):
        """after_insert should be a no-op when ignore_erpnext_sync flag is set."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        before = frappe.db.count("HD Customer")

        make_erp_customer("Test Loop Guard ERP", ignore_sync=True)

        after = frappe.db.count("HD Customer")
        self.assertEqual(
            before, after, "No HD Customer should be created when loop guard is set"
        )

    def test_erp_customer_insert_skips_when_already_synced(self):
        """after_insert should not create an HD Customer when hd_customer is already set."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        # Pre-create an unlinked HD Customer and an ERPNext Customer, then link them manually
        hd_doc = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test ERP Already Synced"}
        )
        hd_doc.flags.ignore_erpnext_sync = True
        hd_doc.insert(ignore_permissions=True)

        erp_doc = make_erp_customer("Test ERP Already Synced", ignore_sync=True)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        frappe.db.set_value(
            "HD Customer", hd_doc.name, "erpnext_customer", erp_doc.name
        )

        before = frappe.db.count("HD Customer")

        # Invoke after_insert directly — the doc already has hd_customer set
        from helpdesk.helpdesk.integrations.erpnext.customer import after_insert

        erp_doc.reload()
        after_insert(erp_doc, method=None)

        after = frappe.db.count("HD Customer")
        self.assertEqual(
            before,
            after,
            "after_insert must not create an HD Customer when already synced",
        )

    # ------------------------------------------------------------------
    # Feature 3: ERPNext on_update → propagate to HD Customer
    # ------------------------------------------------------------------

    def test_erp_customer_on_update_propagates_customer_name_to_hd(self):
        """Saving an ERPNext Customer with a changed customer_name should update the linked HD Customer."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        hd_doc = make_hd_customer("Test Update Propagation")
        hd_doc.reload()
        erp_name = hd_doc.erpnext_customer
        self.assertTrue(erp_name, "HD Customer must have erpnext_customer set")

        erp_doc = frappe.get_doc("Customer", erp_name)
        erp_doc.customer_name = "Test Update Propagation Updated"
        erp_doc.save()

        hd_doc.reload()
        self.assertEqual(
            hd_doc.customer_name,
            "Test Update Propagation Updated",
            "HD Customer.customer_name should be updated by the on_update hook",
        )

    # ------------------------------------------------------------------
    # Feature 8: HD Customer on_update → propagate to ERPNext Customer
    # ------------------------------------------------------------------

    def test_hd_customer_on_update_propagates_image_to_erpnext(self):
        """Saving an HD Customer with a changed image should update the linked ERPNext Customer."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        hd_doc = make_hd_customer("Test HD Update To ERP")
        hd_doc.reload()
        erp_name = hd_doc.erpnext_customer
        self.assertTrue(
            erp_name, "HD Customer must have erpnext_customer set after insert"
        )

        hd_doc.image = "/files/test-avatar.png"
        hd_doc.save()

        updated_image = frappe.db.get_value("Customer", erp_name, "image")
        self.assertEqual(
            updated_image,
            "/files/test-avatar.png",
            "ERPNext Customer.image should be updated by the HD Customer on_update hook",
        )

    def test_hd_customer_on_update_skips_when_nothing_changed(self):
        """Saving an HD Customer without changing customer_name or image should not write to ERPNext."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        hd_doc = make_hd_customer("Test HD Update No Change")
        hd_doc.reload()
        erp_name = hd_doc.erpnext_customer
        self.assertTrue(erp_name)

        # Touch a field that is not customer_name or image
        hd_doc.domain = "test.example.com"
        hd_doc.save()

        # customer_name on ERPNext side should still match the original
        erp_customer_name = frappe.db.get_value("Customer", erp_name, "customer_name")
        self.assertEqual(
            erp_customer_name,
            "Test HD Update No Change",
            "ERPNext customer_name should be unchanged when unrelated HD fields are updated",
        )

    def test_hd_customer_on_update_skips_when_loop_guard_set(self):
        """sync_update_to_erpnext should be a no-op when ignore_erpnext_sync flag is set."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        hd_doc = make_hd_customer("Test HD Update Loop Guard")
        hd_doc.reload()
        erp_name = hd_doc.erpnext_customer
        self.assertTrue(erp_name)

        original_name = frappe.db.get_value("Customer", erp_name, "customer_name")

        hd_doc.flags.ignore_erpnext_sync = True
        hd_doc.image = "/files/should-not-propagate.png"
        hd_doc.save()

        erp_image = frappe.db.get_value("Customer", erp_name, "image")
        self.assertNotEqual(
            erp_image,
            "/files/should-not-propagate.png",
            "ERPNext Customer should not be updated when loop guard is set",
        )

    # ------------------------------------------------------------------
    # Features 5 & 6: sync_all_customers_with_erpnext
    # ------------------------------------------------------------------

    @patch("frappe.get_installed_apps", return_value=ERPNEXT_NOT_INSTALLED)
    def test_sync_all_skips_when_erpnext_not_installed(self, _mock):
        """sync_all_customers_with_erpnext should exit early if ERPNext is not installed."""
        from helpdesk.helpdesk.integrations.erpnext.customer import (
            sync_all_customers_with_erpnext,
        )

        result = sync_all_customers_with_erpnext()
        self.assertEqual(result["status"], "skipped")

    def test_sync_all_links_unsynced_customers_in_both_directions(self):
        """sync_all_customers_with_erpnext should sync unlinked HD and ERPNext Customers."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        # Create 2 unsynced HD Customers
        hd1 = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Sync All HD 1"}
        )
        hd1.flags.ignore_erpnext_sync = True
        hd1.insert(ignore_permissions=True)

        hd2 = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Sync All HD 2"}
        )
        hd2.flags.ignore_erpnext_sync = True
        hd2.insert(ignore_permissions=True)

        # Create 1 unsynced ERPNext Customer
        erp1 = make_erp_customer("Test Sync All ERP 1", ignore_sync=True)

        from helpdesk.helpdesk.integrations.erpnext.customer import (
            sync_all_customers_with_erpnext,
        )

        result = sync_all_customers_with_erpnext()

        # Both unsynced HD Customers should have been synced to ERPNext
        self.assertGreaterEqual(result["created_in_erpnext"], 2)
        # The unsynced ERPNext Customer should have been synced to HD
        self.assertGreaterEqual(result["created_in_hd"], 1)

        # Verify actual links were created
        hd1.reload()
        self.assertTrue(
            hd1.erpnext_customer, "HD Customer 1 should have erpnext_customer set"
        )
        hd2.reload()
        self.assertTrue(
            hd2.erpnext_customer, "HD Customer 2 should have erpnext_customer set"
        )
        self.assertTrue(
            frappe.db.get_value("Customer", erp1.name, "hd_customer"),
            "ERPNext Customer should have hd_customer set",
        )
