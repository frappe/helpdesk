# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.model.rename_doc import rename_doc
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import (
    disable_erpnext_sync,
    enable_erpnext_sync,
    make_hd_customer,
)


class TestHDCustomer(FrappeTestCase):
    def setUp(self):
        disable_erpnext_sync()

    def test_after_insert_no_erp_customer_when_sync_disabled(self):
        """No ERP Customer should be created when integration is off."""
        doc = make_hd_customer("Sync Disabled Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", doc.name, force=True)

        erp_exists = frappe.db.exists("Customer", {"hd_customer": doc.name})
        self.assertFalse(erp_exists)

    def test_after_insert_creates_erp_customer_when_sync_enabled(self):
        """Inserting an HD Customer with sync on should create a linked ERP Customer."""
        enable_erpnext_sync()

        doc = frappe.get_doc(
            {"doctype": "HD Customer", "customer_name": "Sync Enabled Co"}
        )
        doc.insert(ignore_permissions=True)
        self.addCleanup(
            frappe.delete_doc,
            "Customer",
            frappe.db.get_value("Customer", {"hd_customer": doc.name}, "name"),
            force=True,
        )
        self.addCleanup(frappe.delete_doc, "HD Customer", doc.name, force=True)

        doc.reload()
        self.assertTrue(doc.erpnext_customer)
        erp_exists = frappe.db.exists("Customer", {"hd_customer": doc.name})
        self.assertTrue(erp_exists)

    def test_after_insert_skips_creation_if_erpnext_customer_already_set(self):
        """If erpnext_customer is already set, no new ERP Customer should be created."""
        enable_erpnext_sync()

        # create an ERP customer manually first
        erp_doc = frappe.get_doc(
            {"doctype": "Customer", "customer_name": "Pre-Linked Co"}
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        hd_doc = frappe.get_doc(
            {
                "doctype": "HD Customer",
                "customer_name": "Pre-Linked Co HD",
                "erpnext_customer": erp_doc.name,
            }
        )
        hd_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        # Only the one we created manually should exist
        count = frappe.db.count("Customer", {"hd_customer": hd_doc.name})
        self.assertEqual(count, 0)  # the erp_doc has no hd_customer link yet

    def test_after_insert_skips_creation_if_erp_customer_already_linked(self):
        """If an ERP Customer already points to this HD Customer, don't create a duplicate."""
        enable_erpnext_sync()

        # insert HD customer without sync to get a name
        hd_doc = make_hd_customer("Already Linked Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        # create ERP Customer that already references this HD Customer
        erp_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Already Linked Co ERP",
                "hd_customer": hd_doc.name,
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        # trigger after_insert path manually (simulate re-insert scenario)
        hd_doc.flags.ignore_erpnext_sync = False
        hd_doc.create_customer_in_erpnext()

        count = frappe.db.count("Customer", {"hd_customer": hd_doc.name})
        self.assertEqual(count, 1)

    def test_on_update_image_not_synced_when_sync_disabled(self):
        """Changing image with sync off should not update ERP Customer image."""
        hd_doc = make_hd_customer("Image No Sync Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Image No Sync Co ERP",
                "hd_customer": hd_doc.name,
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        hd_doc.image = "/files/new_logo.png"
        hd_doc.save(ignore_permissions=True)

        erp_image = frappe.db.get_value("Customer", erp_doc.name, "image")
        self.assertNotEqual(erp_image, "/files/new_logo.png")

    def test_on_update_image_syncs_to_erp_customer(self):
        """Changing image with sync on should update the linked ERP Customer image."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Image Sync Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Image Sync Co ERP",
                "hd_customer": hd_doc.name,
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        hd_doc.image = "/files/new_logo.png"
        hd_doc.flags.ignore_erpnext_sync = False
        hd_doc.save(ignore_permissions=True)

        erp_image = frappe.db.get_value("Customer", erp_doc.name, "image")
        self.assertEqual(erp_image, "/files/new_logo.png")

    def test_on_update_image_no_error_when_no_linked_erp_customer(self):
        """Changing image when no ERP Customer is linked should not raise."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Image No Link Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        hd_doc.image = "/files/logo.png"
        hd_doc.flags.ignore_erpnext_sync = False
        try:
            hd_doc.save(ignore_permissions=True)
        except Exception as e:
            self.fail(f"save raised unexpectedly: {e}")

    def test_after_rename_updates_hd_customer_on_erp(self):
        """Renaming an HD Customer should update hd_customer on the linked ERP Customer."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Rename Source Co")
        self.addCleanup(
            frappe.delete_doc, "HD Customer", "Rename Target Co", force=True
        )

        erp_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Rename Source Co ERP",
                "hd_customer": hd_doc.name,
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        rename_doc(
            doctype="HD Customer",
            old=hd_doc.name,
            new="Rename Target Co",
            ignore_permissions=True,
        )

        updated = frappe.db.get_value("Customer", erp_doc.name, "hd_customer")
        self.assertEqual(updated, "Rename Target Co")

    def test_after_rename_skipped_when_sync_disabled(self):
        """Renaming with sync off should not update hd_customer on ERP Customer."""
        hd_doc = make_hd_customer("Rename No Sync Co")
        self.addCleanup(
            frappe.delete_doc, "HD Customer", "Rename No Sync Target", force=True
        )

        erp_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": "Rename No Sync ERP",
                "hd_customer": hd_doc.name,
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        rename_doc(
            doctype="HD Customer",
            old=hd_doc.name,
            new="Rename No Sync Target",
            ignore_permissions=True,
        )

        updated = frappe.db.get_value("Customer", erp_doc.name, "hd_customer")
        self.assertEqual(updated, hd_doc.name)  # unchanged

    def test_after_rename_no_error_when_no_linked_erp_customer(self):
        """Renaming an HD Customer with no ERP link should not raise."""
        hd_doc = make_hd_customer("Rename Orphan Co")
        self.addCleanup(
            frappe.delete_doc, "HD Customer", "Rename Orphan Target", force=True
        )

        enable_erpnext_sync()
        try:
            rename_doc(
                doctype="HD Customer",
                old=hd_doc.name,
                new="Rename Orphan Target",
                ignore_permissions=True,
            )
        except Exception as e:
            self.fail(f"rename raised unexpectedly: {e}")

    def tearDown(self):
        disable_erpnext_sync()
