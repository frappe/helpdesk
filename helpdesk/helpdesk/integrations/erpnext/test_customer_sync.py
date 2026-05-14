# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import ERPNEXT_NOT_INSTALLED, make_erp_customer


class TestCustomerSyncAPI(FrappeTestCase):
    """Integration tests for helpdesk/helpdesk/integrations/erpnext/customer.py sync functions."""

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
    # bulk_sync_erpnext_customers_to_hd
    # ------------------------------------------------------------------

    def test_bulk_sync_returns_correct_counts(self):
        """bulk_sync should create HD Customers for unlinked ERPNext Customers and skip linked ones."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        erp1 = make_erp_customer("Test Bulk C1")
        erp2 = make_erp_customer("Test Bulk C2")
        erp3 = make_erp_customer("Test Bulk C3")

        # Pre-link erp2 — it should be skipped during bulk sync
        hd_for_erp2 = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Bulk C2 HD"}
        )
        hd_for_erp2.flags.ignore_erpnext_sync = True
        hd_for_erp2.insert(ignore_permissions=True)
        frappe.db.set_value("Customer", erp2.name, "hd_customer", hd_for_erp2.name)
        frappe.db.set_value(
            "HD Customer", hd_for_erp2.name, "erpnext_customer", erp2.name
        )

        from helpdesk.helpdesk.integrations.erpnext.customer import (
            bulk_sync_erpnext_customers_to_hd,
        )

        result = bulk_sync_erpnext_customers_to_hd([erp1.name, erp2.name, erp3.name])

        self.assertEqual(result["created"], 2)
        self.assertEqual(result["skipped"], 1)

        # Verify the newly linked customers are actually linked
        self.assertTrue(frappe.db.get_value("Customer", erp1.name, "hd_customer"))
        self.assertTrue(frappe.db.get_value("Customer", erp3.name, "hd_customer"))

    def test_bulk_sync_all_already_synced(self):
        """bulk_sync should skip all customers that are already linked."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        erp1 = make_erp_customer("Test Bulk All Synced C1")
        erp2 = make_erp_customer("Test Bulk All Synced C2")

        for erp_doc in (erp1, erp2):
            hd = frappe.get_doc(
                {
                    "doctype": "HD Customer",
                    "customer_name": f"{erp_doc.customer_name} HD",
                }
            )
            hd.flags.ignore_erpnext_sync = True
            hd.insert(ignore_permissions=True)
            frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd.name)
            frappe.db.set_value(
                "HD Customer", hd.name, "erpnext_customer", erp_doc.name
            )

        from helpdesk.helpdesk.integrations.erpnext.customer import (
            bulk_sync_erpnext_customers_to_hd,
        )

        result = bulk_sync_erpnext_customers_to_hd([erp1.name, erp2.name])

        self.assertEqual(result["created"], 0)
        self.assertEqual(result["skipped"], 2)

    def test_bulk_sync_empty_list(self):
        """bulk_sync with an empty list should return zeroes without error."""
        from helpdesk.helpdesk.integrations.erpnext.customer import (
            bulk_sync_erpnext_customers_to_hd,
        )

        result = bulk_sync_erpnext_customers_to_hd([])
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["skipped"], 0)

    # ------------------------------------------------------------------
    # _sync_hd_to_erpnext
    # ------------------------------------------------------------------

    def test_sync_hd_to_erpnext_creates_erp_customers(self):
        """_sync_hd_to_erpnext should create ERPNext Customers for each unsynced HD Customer."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        hd1 = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Sync HtoE 1"}
        )
        hd1.flags.ignore_erpnext_sync = True
        hd1.insert(ignore_permissions=True)

        hd2 = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Sync HtoE 2"}
        )
        hd2.flags.ignore_erpnext_sync = True
        hd2.insert(ignore_permissions=True)

        from helpdesk.helpdesk.integrations.erpnext.customer import sync_hd_to_erpnext

        count = sync_hd_to_erpnext()

        self.assertGreaterEqual(count, 2)

        hd1.reload()
        self.assertTrue(
            hd1.erpnext_customer, "HD Customer 1 should have erpnext_customer set"
        )
        hd2.reload()
        self.assertTrue(
            hd2.erpnext_customer, "HD Customer 2 should have erpnext_customer set"
        )

    def test_sync_hd_to_erpnext_logs_error_and_continues(self):
        """_sync_hd_to_erpnext should log errors per customer and keep processing remaining ones."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        bad_hd = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Sync HtoE Error Bad"}
        )
        bad_hd.flags.ignore_erpnext_sync = True
        bad_hd.insert(ignore_permissions=True)

        good_hd = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Test Sync HtoE Error Good"}
        )
        good_hd.flags.ignore_erpnext_sync = True
        good_hd.insert(ignore_permissions=True)

        original_get_doc = frappe.get_doc

        def patched_get_doc(doctype, name=None, *args, **kwargs):
            doc = original_get_doc(doctype, name, *args, **kwargs)
            if doctype == "HD Customer" and name == bad_hd.name:

                def failing_sync():
                    raise Exception("Simulated ERPNext insert failure")

                doc.sync_to_erpnext = failing_sync
            return doc

        with (
            patch("frappe.get_doc", side_effect=patched_get_doc),
            patch("frappe.log_error") as mock_log,
        ):
            from helpdesk.helpdesk.integrations.erpnext.customer import (
                sync_hd_to_erpnext,
            )

            count = sync_hd_to_erpnext()

        mock_log.assert_called()

        # good_hd should have been synced despite bad_hd failing
        good_hd.reload()
        self.assertTrue(
            good_hd.erpnext_customer,
            "good_hd should be synced even though bad_hd failed",
        )

    # ------------------------------------------------------------------
    # _sync_erpnext_to_hd
    # ------------------------------------------------------------------

    def test_sync_erpnext_to_hd_creates_hd_customers(self):
        """_sync_erpnext_to_hd should create HD Customers for each unsynced ERPNext Customer."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        erp1 = make_erp_customer("Test Sync EtoH 1")
        erp2 = make_erp_customer("Test Sync EtoH 2")

        from helpdesk.helpdesk.integrations.erpnext.customer import sync_erpnext_to_hd

        count = sync_erpnext_to_hd()

        self.assertGreaterEqual(count, 2)

        self.assertTrue(
            frappe.db.get_value("Customer", erp1.name, "hd_customer"),
            "ERPNext Customer 1 should have hd_customer set",
        )
        self.assertTrue(
            frappe.db.get_value("Customer", erp2.name, "hd_customer"),
            "ERPNext Customer 2 should have hd_customer set",
        )

    def test_sync_erpnext_to_hd_logs_error_and_continues(self):
        """_sync_erpnext_to_hd should log errors per customer and keep processing remaining ones."""
        if "erpnext" not in frappe.get_installed_apps():
            self.skipTest("ERPNext not installed")

        bad_erp = make_erp_customer("Test Sync EtoH Error Bad")
        good_erp = make_erp_customer("Test Sync EtoH Error Good")

        original_sync = None

        def patched_sync_erp_to_hd(doc):
            if doc.name == bad_erp.name:
                raise Exception("Simulated HD Customer insert failure")
            return original_sync(doc)

        from helpdesk.helpdesk.integrations.erpnext import customer as customer_module

        original_sync = customer_module.create_or_link_hd_customer

        with (
            patch.object(
                customer_module,
                "create_or_link_hd_customer",
                side_effect=patched_sync_erp_to_hd,
            ),
            patch("frappe.log_error") as mock_log,
        ):
            from helpdesk.helpdesk.integrations.erpnext.customer import (
                sync_erpnext_to_hd,
            )

            count = sync_erpnext_to_hd()

        mock_log.assert_called()

        # good_erp should have been synced despite bad_erp failing
        self.assertTrue(
            frappe.db.get_value("Customer", good_erp.name, "hd_customer"),
            "good_erp should be synced even though bad_erp failed",
        )

    # ------------------------------------------------------------------
    # is_unsynced
    # ------------------------------------------------------------------

    @patch("frappe.get_installed_apps", return_value=ERPNEXT_NOT_INSTALLED)
    def test_is_unsynced_returns_false_when_erpnext_not_installed(self, _mock):
        """is_unsynced should return False immediately when ERPNext is not installed."""
        from helpdesk.helpdesk.integrations.erpnext.customer import is_unsynced

        self.assertFalse(is_unsynced())
