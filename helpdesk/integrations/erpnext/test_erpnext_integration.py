# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.model.rename_doc import rename_doc
from frappe.tests.utils import FrappeTestCase

from helpdesk.integrations.erpnext.user_permission import sync_user_permissions

from .test_utils import (
    disable_erpnext_sync,
    enable_erpnext_sync,
    make_erpnext_customer,
    make_hd_customer,
    make_user_permission,
    make_user_permission_no_sync,
)


class TestERPNextIntegration(FrappeTestCase):
    def setUp(self):
        disable_erpnext_sync()

    def tearDown(self):
        disable_erpnext_sync()

    # ------------------------------------------------------------------
    # after_insert
    # ------------------------------------------------------------------

    def test_after_insert_no_erp_customer_when_sync_disabled(self):
        """No ERP Customer should be created when integration is off."""
        doc = make_hd_customer("Sync Disabled Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", doc.name, force=True)

        self.assertFalse(frappe.db.exists("Customer", {"hd_customer": doc.name}))

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
        self.assertTrue(frappe.db.exists("Customer", {"hd_customer": doc.name}))

    def test_after_insert_skips_creation_if_erpnext_customer_already_set(self):
        """If erpnext_customer is already set, no new ERP Customer should be created."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("Pre-Linked Co")
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

        # erp_doc has no hd_customer link — count should be zero
        self.assertEqual(frappe.db.count("Customer", {"hd_customer": hd_doc.name}), 0)

    def test_after_insert_skips_creation_if_erp_customer_already_linked(self):
        """If an ERP Customer already points to this HD Customer, don't create a duplicate."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Already Linked Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_doc = make_erpnext_customer(
            "Already Linked Co ERP", hd_customer=hd_doc.name
        )
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        hd_doc.flags.ignore_erpnext_sync = False
        hd_doc.create_customer_in_erpnext()

        self.assertEqual(frappe.db.count("Customer", {"hd_customer": hd_doc.name}), 1)

    # ------------------------------------------------------------------
    # on_update (image sync)
    # ------------------------------------------------------------------

    def test_on_update_image_not_synced_when_sync_disabled(self):
        """Changing image with sync off should not update ERP Customer image."""
        hd_doc = make_hd_customer("Image No Sync Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_doc = make_erpnext_customer("Image No Sync Co ERP", hd_customer=hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        hd_doc.image = "/files/new_logo.png"
        hd_doc.save(ignore_permissions=True)

        self.assertNotEqual(
            frappe.db.get_value("Customer", erp_doc.name, "image"),
            "/files/new_logo.png",
        )

    def test_on_update_image_syncs_to_erp_customer(self):
        """Changing image with sync on should update the linked ERP Customer image."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Image Sync Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_doc = make_erpnext_customer("Image Sync Co ERP", hd_customer=hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        hd_doc.erpnext_customer = erp_doc.name
        hd_doc.image = "/files/new_logo.png"
        hd_doc.flags.ignore_erpnext_sync = False
        hd_doc.save(ignore_permissions=True)

        self.assertEqual(
            frappe.db.get_value("Customer", erp_doc.name, "image"),
            "/files/new_logo.png",
        )

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

    # ------------------------------------------------------------------
    # after_rename
    # ------------------------------------------------------------------

    def test_after_rename_updates_hd_customer_on_erp(self):
        """Renaming an HD Customer should cascade-rename the linked ERP Customer."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Rename Source Co")
        self.addCleanup(
            frappe.delete_doc, "HD Customer", "Rename Target Co", force=True
        )
        self.addCleanup(frappe.delete_doc, "Customer", "Rename Target Co", force=True)

        erp_doc = make_erpnext_customer("Rename Source Co ERP", hd_customer=hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        frappe.db.set_value(
            "HD Customer", hd_doc.name, "erpnext_customer", erp_doc.name
        )

        rename_doc(
            doctype="HD Customer",
            old=hd_doc.name,
            new="Rename Target Co",
            ignore_permissions=True,
        )

        # ERP counterpart was cascade-renamed
        self.assertFalse(frappe.db.exists("Customer", erp_doc.name))
        self.assertTrue(frappe.db.exists("Customer", "Rename Target Co"))
        self.assertEqual(
            frappe.db.get_value("Customer", "Rename Target Co", "hd_customer"),
            "Rename Target Co",
        )

    def test_after_rename_skipped_when_sync_disabled(self):
        """Renaming with sync off should not update hd_customer on ERP Customer."""
        hd_doc = make_hd_customer("Rename No Sync Co")
        self.addCleanup(
            frappe.delete_doc, "HD Customer", "Rename No Sync Target", force=True
        )

        erp_doc = make_erpnext_customer("Rename No Sync ERP", hd_customer=hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        rename_doc(
            doctype="HD Customer",
            old=hd_doc.name,
            new="Rename No Sync Target",
            ignore_permissions=True,
        )

        self.assertEqual(
            frappe.db.get_value("Customer", erp_doc.name, "hd_customer"), hd_doc.name
        )

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

    # ------------------------------------------------------------------
    # on_trash
    # ------------------------------------------------------------------

    def test_hd_customer_deletion_deletes_linked_erp_customer(self):
        """Deleting an HD Customer should delete the linked ERPNext Customer."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Trash HD Co")
        erp_doc = make_erpnext_customer("Trash HD Co ERP", hd_customer=hd_doc.name)
        frappe.db.set_value(
            "HD Customer", hd_doc.name, "erpnext_customer", erp_doc.name
        )
        erp_name = erp_doc.name

        frappe.delete_doc("HD Customer", hd_doc.name, force=True)

        self.assertFalse(frappe.db.exists("Customer", erp_name))

    def test_hd_customer_deletion_no_error_when_no_linked_erp_customer(self):
        """Deleting an HD Customer with no ERP link should not raise."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("Trash Orphan HD Co")
        try:
            frappe.delete_doc("HD Customer", hd_doc.name, force=True)
        except Exception as e:
            self.fail(f"delete raised unexpectedly: {e}")

    def test_hd_customer_deletion_skipped_when_sync_disabled(self):
        """Deleting an HD Customer with sync off should leave ERP Customer intact."""
        hd_doc = make_hd_customer("Trash No Sync HD Co")
        erp_doc = make_erpnext_customer("Trash No Sync ERP Co", hd_customer=hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        frappe.db.set_value(
            "HD Customer", hd_doc.name, "erpnext_customer", erp_doc.name
        )

        frappe.delete_doc("HD Customer", hd_doc.name, force=True)

        self.assertTrue(frappe.db.exists("Customer", erp_doc.name))

    def test_erpnext_customer_deletion_deletes_linked_hd_customer(self):
        """Deleting an ERPNext Customer should delete the linked HD Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("Trash ERP Co")
        hd_doc = make_hd_customer("Trash ERP Co HD", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        hd_name = hd_doc.name

        frappe.delete_doc("Customer", erp_doc.name, force=True)

        self.assertFalse(frappe.db.exists("HD Customer", hd_name))

    def test_erpnext_customer_deletion_no_error_when_no_linked_hd_customer(self):
        """Deleting an ERPNext Customer with no HD link should not raise."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("Trash Orphan ERP Co")
        try:
            frappe.delete_doc("Customer", erp_doc.name, force=True)
        except Exception as e:
            self.fail(f"delete raised unexpectedly: {e}")

    def test_erpnext_customer_deletion_skipped_when_sync_disabled(self):
        """Deleting an ERPNext Customer with sync off should leave HD Customer intact."""
        erp_doc = make_erpnext_customer("Trash No Sync ERP Co")
        hd_doc = make_hd_customer("Trash No Sync HD Co", erpnext_customer=erp_doc.name)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)

        frappe.delete_doc("Customer", erp_doc.name, force=True)

        self.assertTrue(frappe.db.exists("HD Customer", hd_doc.name))

    # ------------------------------------------------------------------
    # sync_user_permissions
    # ------------------------------------------------------------------

    def _cleanup_user_perms(self, user, allow, for_value):
        """Remove a User Permission record if it exists (used as addCleanup target)."""
        name = frappe.db.get_value(
            "User Permission", {"user": user, "allow": allow, "for_value": for_value}
        )
        if name:
            frappe.delete_doc("User Permission", name, force=True)

    def test_sync_skipped_when_sync_disabled(self):
        """sync_user_permissions should do nothing when integration is off."""
        erp_doc = make_erpnext_customer("UP Skip ERP Co")
        hd_doc = make_hd_customer("UP Skip HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "Customer", erp_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            self._cleanup_user_perms, "Administrator", "HD Customer", hd_doc.name
        )

        # sync is disabled — should not mirror the perm
        sync_user_permissions()

        self.assertFalse(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": hd_doc.name,
                },
            )
        )

    # ------------------------------------------------------------------
    # mirror_user_permission_on_trash (real-time delete sync)
    # ------------------------------------------------------------------

    def test_realtime_user_perm_trash_from_hd_deletes_erp_perm(self):
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT Trash UP ERP Co")
        hd_doc = make_hd_customer("RT Trash UP HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        hd_perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        mirrored_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp_doc.name},
        )
        self.assertTrue(mirrored_name)

        frappe.delete_doc("User Permission", hd_perm.name, force=True)

        self.assertFalse(frappe.db.exists("User Permission", mirrored_name))

    def test_realtime_user_perm_trash_from_erp_deletes_hd_perm(self):
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT Trash UP ERP Side Co")
        hd_doc = make_hd_customer(
            "RT Trash UP HD Side Co", erpnext_customer=erp_doc.name
        )
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_perm = make_user_permission("Administrator", "Customer", erp_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", erp_perm.name, force=True)

        mirrored_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "HD Customer", "for_value": hd_doc.name},
        )
        self.assertTrue(mirrored_name)

        frappe.delete_doc("User Permission", erp_perm.name, force=True)

        self.assertFalse(frappe.db.exists("User Permission", mirrored_name))

    def test_realtime_user_perm_trash_no_mirror_delete_when_sync_disabled(self):
        erp_doc = make_erpnext_customer("RT Trash UP Disabled ERP Co")
        hd_doc = make_hd_customer(
            "RT Trash UP Disabled HD Co", erpnext_customer=erp_doc.name
        )
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_perm = make_user_permission_no_sync(
            "Administrator", "Customer", erp_doc.name
        )
        hd_perm = make_user_permission_no_sync(
            "Administrator", "HD Customer", hd_doc.name
        )
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        frappe.delete_doc("User Permission", erp_perm.name, force=True)

        self.assertTrue(frappe.db.exists("User Permission", hd_perm.name))

    # ------------------------------------------------------------------
    # mirror_doc_share_on_trash (real-time delete sync)
    # ------------------------------------------------------------------

    def test_realtime_doc_share_trash_from_hd_deletes_erp_share(self):
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT Trash DS ERP Co")
        hd_doc = make_hd_customer("RT Trash DS HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        hd_share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        hd_share.flags.ignore_share_permission = True
        hd_share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        mirrored_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
            },
        )
        self.assertTrue(mirrored_name)

        frappe.delete_doc("DocShare", hd_share.name, force=True)

        self.assertFalse(frappe.db.exists("DocShare", mirrored_name))

    def test_realtime_doc_share_trash_from_erp_deletes_hd_share(self):
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT Trash DS ERP Side Co")
        hd_doc = make_hd_customer(
            "RT Trash DS HD Side Co", erpnext_customer=erp_doc.name
        )
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        erp_share.flags.ignore_share_permission = True
        erp_share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", erp_share.name, force=True)

        mirrored_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
            },
        )
        self.assertTrue(mirrored_name)

        frappe.delete_doc("DocShare", erp_share.name, force=True)

        self.assertFalse(frappe.db.exists("DocShare", mirrored_name))

    def test_realtime_doc_share_trash_no_mirror_delete_when_sync_disabled(self):
        erp_doc = make_erpnext_customer("RT Trash DS Disabled ERP Co")
        hd_doc = make_hd_customer(
            "RT Trash DS Disabled HD Co", erpnext_customer=erp_doc.name
        )
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        erp_share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        erp_share.flags.ignore_erpnext_sync = True
        erp_share.flags.ignore_share_permission = True
        erp_share.insert(ignore_permissions=True)

        hd_share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        hd_share.flags.ignore_erpnext_sync = True
        hd_share.flags.ignore_share_permission = True
        hd_share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        frappe.delete_doc("DocShare", erp_share.name, force=True)

        self.assertTrue(frappe.db.exists("DocShare", hd_share.name))

    # ------------------------------------------------------------------
    # DocShare mirroring tests
    # ------------------------------------------------------------------

    def test_realtime_hd_doc_share_mirrors_to_erp_when_enabled(self):
        """Creating a DocShare for HD Customer should auto-create one for linked ERP Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT DS ERP Mirror Co")
        hd_doc = make_hd_customer("RT DS HD Mirror Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
                "read": 1,
                "write": 1,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        share.flags.ignore_share_permission = True
        share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", share.name, force=True)

        mirrored = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
            },
            ["name", "read", "write", "share", "submit"],
            as_dict=True,
        )
        self.assertTrue(mirrored)
        self.addCleanup(frappe.delete_doc, "DocShare", mirrored.name, force=True)
        self.assertEqual(mirrored.read, 1)
        self.assertEqual(mirrored.write, 1)
        self.assertEqual(mirrored.share, 0)
        self.assertEqual(mirrored.submit, 0)

    def test_realtime_erp_doc_share_mirrors_to_hd_when_enabled(self):
        """Creating a DocShare for Customer should auto-create one for linked HD Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT DS ERP To HD Co")
        hd_doc = make_hd_customer("RT DS HD To ERP Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
                "read": 1,
                "write": 0,
                "share": 1,
                "submit": 0,
                "everyone": 0,
            }
        )
        share.flags.ignore_share_permission = True
        share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", share.name, force=True)

        self.assertTrue(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "HD Customer",
                    "share_name": hd_doc.name,
                },
            )
        )

    def test_realtime_doc_share_not_mirrored_when_sync_disabled(self):
        """Creating a DocShare with sync off should not create mirrored share."""
        erp_doc = make_erpnext_customer("RT DS Disabled ERP Co")
        hd_doc = make_hd_customer("RT DS Disabled HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        share.flags.ignore_share_permission = True
        share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", share.name, force=True)

        self.assertFalse(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "HD Customer",
                    "share_name": hd_doc.name,
                },
            )
        )

    def test_realtime_doc_share_not_duplicated_if_mirror_exists(self):
        """If mirrored DocShare exists already, hook should not create a duplicate."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT DS No Dup ERP Co")
        hd_doc = make_hd_customer("RT DS No Dup HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        existing = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        existing.flags.ignore_erpnext_sync = True
        existing.flags.ignore_share_permission = True
        existing.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", existing.name, force=True)

        share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        share.flags.ignore_share_permission = True
        share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", share.name, force=True)

        self.assertEqual(
            frappe.db.count(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "Customer",
                    "share_name": erp_doc.name,
                },
            ),
            1,
        )

    def test_realtime_doc_share_not_mirrored_when_unlinked(self):
        """Creating DocShare for unlinked customer should not mirror."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("RT DS Unlinked HD Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        share.flags.ignore_share_permission = True
        share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", share.name, force=True)

        self.assertFalse(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "Customer",
                    "share_name": hd_doc.name,
                },
            )
        )

    def test_realtime_doc_share_unrelated_doctype_not_affected(self):
        """Creating DocShare for unrelated doctype should not create mirrored share."""
        enable_erpnext_sync()

        share = frappe.get_doc(
            {
                "doctype": "DocShare",
                "user": "Administrator",
                "share_doctype": "DocType",
                "share_name": "HD Ticket",
                "read": 1,
                "write": 0,
                "share": 0,
                "submit": 0,
                "everyone": 0,
            }
        )
        share.flags.ignore_share_permission = True
        share.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "DocShare", share.name, force=True)

        self.assertFalse(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "HD Customer",
                    "share_name": "HD Ticket",
                },
            )
        )

    # ------------------------------------------------------------------
    # User Permissions mirroring test
    # ------------------------------------------------------------------

    def test_erp_perm_mirrored_to_hd_customer(self):
        """A User Permission on Customer should be mirrored to the linked HD Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("UP ERP Mirror Co")
        hd_doc = make_hd_customer("UP ERP Mirror HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "Customer", erp_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            self._cleanup_user_perms, "Administrator", "HD Customer", hd_doc.name
        )

        sync_user_permissions()

        self.assertTrue(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": hd_doc.name,
                },
            )
        )

    def test_hd_perm_mirrored_to_erp_customer(self):
        """A User Permission on HD Customer should be mirrored to the linked ERP Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("UP HD Mirror ERP Co")
        hd_doc = make_hd_customer("UP HD Mirror Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            self._cleanup_user_perms, "Administrator", "Customer", erp_doc.name
        )

        sync_user_permissions()

        self.assertTrue(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": erp_doc.name,
                },
            )
        )

    def test_no_duplicate_perm_created_if_already_exists(self):
        """sync_user_permissions should not create a duplicate if the mirrored perm already exists."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("UP No Dup ERP Co")
        hd_doc = make_hd_customer("UP No Dup HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        # Use no-sync variants so the real-time hook doesn't fire during setup —
        # we want to test the bulk sync deduplication path, not the hook path.
        erp_perm = make_user_permission_no_sync(
            "Administrator", "Customer", erp_doc.name
        )
        hd_perm = make_user_permission_no_sync(
            "Administrator", "HD Customer", hd_doc.name
        )
        self.addCleanup(frappe.delete_doc, "User Permission", erp_perm.name, force=True)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        sync_user_permissions()

        # Still exactly one perm for each side — no duplicates
        self.assertEqual(
            frappe.db.count(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": hd_doc.name,
                },
            ),
            1,
        )
        self.assertEqual(
            frappe.db.count(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": erp_doc.name,
                },
            ),
            1,
        )

    def test_perm_not_mirrored_when_customers_not_linked(self):
        """A User Permission on an unlinked Customer should not produce an HD Customer perm."""
        enable_erpnext_sync()

        # erp_doc has no hd_customer back-link
        erp_doc = make_erpnext_customer("UP Unlinked ERP Co")
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)

        perm = make_user_permission("Administrator", "Customer", erp_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)

        sync_user_permissions()

        # No HD Customer perm should have been created
        self.assertFalse(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": erp_doc.name,
                },
            )
        )

    def test_apply_to_all_doctypes_preserved_on_mirror(self):
        """The apply_to_all_doctypes flag should be carried over to the mirrored perm."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("UP Flag ERP Co")
        hd_doc = make_hd_customer("UP Flag HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        # create perm with apply_to_all_doctypes = 0
        perm = make_user_permission(
            "Administrator", "Customer", erp_doc.name, apply_to_all_doctypes=0
        )
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            self._cleanup_user_perms, "Administrator", "HD Customer", hd_doc.name
        )

        sync_user_permissions()

        mirrored_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "HD Customer", "for_value": hd_doc.name},
            "name",
        )
        self.assertTrue(mirrored_name)
        mirrored_flag = frappe.db.get_value(
            "User Permission", mirrored_name, "apply_to_all_doctypes"
        )
        self.assertEqual(mirrored_flag, 0)

    # ------------------------------------------------------------------
    # mirror_user_permission_on_insert (real-time sync)
    # ------------------------------------------------------------------

    def test_realtime_hd_customer_perm_mirrors_to_erp_when_enabled(self):
        """Creating a User Permission for HD Customer should auto-create one for the linked ERP Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT ERP Mirror Co")
        hd_doc = make_hd_customer("RT HD Mirror Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            self._cleanup_user_perms, "Administrator", "Customer", erp_doc.name
        )

        self.assertTrue(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": erp_doc.name,
                },
            )
        )

    def test_realtime_erp_customer_perm_mirrors_to_hd_when_enabled(self):
        """Creating a User Permission for Customer should auto-create one for the linked HD Customer."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT ERP To HD Co")
        hd_doc = make_hd_customer("RT HD To ERP Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "Customer", erp_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            self._cleanup_user_perms, "Administrator", "HD Customer", hd_doc.name
        )

        self.assertTrue(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": hd_doc.name,
                },
            )
        )

    def test_realtime_perm_not_mirrored_when_sync_disabled(self):
        """Creating a User Permission when sync is off should not create a mirrored perm."""
        # sync is disabled (setUp calls disable_erpnext_sync)

        erp_doc = make_erpnext_customer("RT Disabled ERP Co")
        hd_doc = make_hd_customer("RT Disabled HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)

        self.assertFalse(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": erp_doc.name,
                },
            )
        )

    def test_realtime_perm_not_duplicated_if_mirror_already_exists(self):
        """If the mirrored perm already exists, no duplicate should be created."""
        enable_erpnext_sync()

        erp_doc = make_erpnext_customer("RT No Dup ERP Co")
        hd_doc = make_hd_customer("RT No Dup HD Co", erpnext_customer=erp_doc.name)
        frappe.db.set_value("Customer", erp_doc.name, "hd_customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "Customer", erp_doc.name, force=True)
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        # Pre-create the mirror without triggering the hook, so it already exists
        # before the triggering perm is inserted.
        existing_mirror = make_user_permission_no_sync(
            "Administrator", "Customer", erp_doc.name
        )
        self.addCleanup(
            frappe.delete_doc, "User Permission", existing_mirror.name, force=True
        )

        # Now create the HD Customer perm — the hook fires but should detect the
        # existing Customer perm and skip creation.
        perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)

        self.assertEqual(
            frappe.db.count(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": erp_doc.name,
                },
            ),
            1,
        )

    def test_realtime_perm_not_mirrored_when_customer_not_linked(self):
        """Creating a perm for an unlinked HD Customer should not produce a Customer perm."""
        enable_erpnext_sync()

        hd_doc = make_hd_customer("RT Unlinked HD Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)

        # hd_doc has no erpnext_customer link — no Customer perm should be created
        self.assertFalse(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": hd_doc.name,
                },
            )
        )

    def test_realtime_perm_unrelated_doctype_not_affected(self):
        """Creating a User Permission for a non-customer doctype should do nothing."""
        enable_erpnext_sync()

        perm = frappe.get_doc(
            {
                "doctype": "User Permission",
                "user": "Administrator",
                "allow": "DocType",
                "for_value": "HD Ticket",
                "apply_to_all_doctypes": 1,
            }
        )
        perm.insert(ignore_permissions=True)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)

        # Verify no unexpected perms were created
        self.assertFalse(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": "HD Ticket",
                },
            )
        )

    # ------------------------------------------------------------------
    # Rename cascade (plain + merge)
    # ------------------------------------------------------------------

    def _make_linked_pair(self, hd_name, erp_name=None):
        """Create an HD/ERP pair with both Data link fields set. Returns (hd, erp)."""
        erp_name = erp_name or hd_name
        hd = make_hd_customer(hd_name)
        erp = make_erpnext_customer(erp_name, hd_customer=hd.name)
        frappe.db.set_value("HD Customer", hd.name, "erpnext_customer", erp.name)
        return hd, erp

    def _safe_delete(self, dt, name):
        if name and frappe.db.exists(dt, name):
            frappe.delete_doc(dt, name, force=True, ignore_permissions=True)

    def test_plain_rename_cascades_hd_to_erp(self):
        """Renaming an HD Customer cascades to rename the linked ERP Customer."""
        enable_erpnext_sync()

        hd, erp = self._make_linked_pair("Cascade HD Old")
        self.addCleanup(self._safe_delete, "HD Customer", "Cascade HD New")
        self.addCleanup(self._safe_delete, "Customer", "Cascade HD New")
        self.addCleanup(self._safe_delete, "HD Customer", hd.name)
        self.addCleanup(self._safe_delete, "Customer", erp.name)

        rename_doc(
            doctype="HD Customer",
            old=hd.name,
            new="Cascade HD New",
            ignore_permissions=True,
        )

        self.assertTrue(frappe.db.exists("HD Customer", "Cascade HD New"))
        self.assertTrue(frappe.db.exists("Customer", "Cascade HD New"))
        self.assertFalse(frappe.db.exists("HD Customer", hd.name))
        self.assertFalse(frappe.db.exists("Customer", erp.name))
        self.assertEqual(
            frappe.db.get_value("HD Customer", "Cascade HD New", "erpnext_customer"),
            "Cascade HD New",
        )
        self.assertEqual(
            frappe.db.get_value("Customer", "Cascade HD New", "hd_customer"),
            "Cascade HD New",
        )

    def test_plain_rename_cascades_erp_to_hd(self):
        """Renaming an ERP Customer cascades to rename the linked HD Customer."""
        enable_erpnext_sync()

        hd, erp = self._make_linked_pair("Cascade ERP Old")
        self.addCleanup(self._safe_delete, "HD Customer", "Cascade ERP New")
        self.addCleanup(self._safe_delete, "Customer", "Cascade ERP New")
        self.addCleanup(self._safe_delete, "HD Customer", hd.name)
        self.addCleanup(self._safe_delete, "Customer", erp.name)

        rename_doc(
            doctype="Customer",
            old=erp.name,
            new="Cascade ERP New",
            ignore_permissions=True,
        )

        self.assertTrue(frappe.db.exists("Customer", "Cascade ERP New"))
        self.assertTrue(frappe.db.exists("HD Customer", "Cascade ERP New"))
        self.assertEqual(
            frappe.db.get_value("HD Customer", "Cascade ERP New", "erpnext_customer"),
            "Cascade ERP New",
        )

    def test_plain_rename_no_cascade_when_no_counterpart(self):
        """Renaming an unlinked HD Customer should not error and not touch ERP side."""
        enable_erpnext_sync()

        hd = make_hd_customer("Lonely HD Old")
        self.addCleanup(self._safe_delete, "HD Customer", "Lonely HD New")
        self.addCleanup(self._safe_delete, "HD Customer", hd.name)

        rename_doc(
            doctype="HD Customer",
            old=hd.name,
            new="Lonely HD New",
            ignore_permissions=True,
        )

        self.assertTrue(frappe.db.exists("HD Customer", "Lonely HD New"))
        self.assertFalse(frappe.db.exists("Customer", "Lonely HD New"))

    def test_plain_rename_blocked_on_other_side_conflict(self):
        """Renaming HD Foo→Bar should fail if an unrelated ERP 'Bar' already exists."""
        enable_erpnext_sync()

        hd, erp = self._make_linked_pair("Conflict HD Old")
        unrelated_erp = make_erpnext_customer("Conflict HD New")
        self.addCleanup(self._safe_delete, "HD Customer", hd.name)
        self.addCleanup(self._safe_delete, "Customer", erp.name)
        self.addCleanup(self._safe_delete, "Customer", unrelated_erp.name)

        with self.assertRaises(frappe.ValidationError):
            rename_doc(
                doctype="HD Customer",
                old=hd.name,
                new="Conflict HD New",
                ignore_permissions=True,
            )

        # Original records untouched
        self.assertTrue(frappe.db.exists("HD Customer", hd.name))
        self.assertTrue(frappe.db.exists("Customer", erp.name))
        self.assertTrue(frappe.db.exists("Customer", unrelated_erp.name))

    def test_merge_transfers_when_target_has_no_counterpart(self):
        """M1: HD Foo (has ERP) merged into HD Bar (no ERP) → ERP Foo transferred to Bar."""
        enable_erpnext_sync()

        # HD Foo has linked ERP "Merge M1 Foo"
        hd_foo, erp_foo = self._make_linked_pair("Merge M1 Foo")
        # HD Bar exists but has no linked ERP
        hd_bar = make_hd_customer("Merge M1 Bar")

        self.addCleanup(self._safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(self._safe_delete, "Customer", hd_bar.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_foo.name)
        self.addCleanup(self._safe_delete, "Customer", erp_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        # HD Foo gone, HD Bar survives
        self.assertFalse(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        # ERP Foo transferred (renamed) to Bar
        self.assertFalse(frappe.db.exists("Customer", erp_foo.name))
        self.assertTrue(frappe.db.exists("Customer", hd_bar.name))
        # Link fields point at each other
        self.assertEqual(
            frappe.db.get_value("HD Customer", hd_bar.name, "erpnext_customer"),
            hd_bar.name,
        )
        self.assertEqual(
            frappe.db.get_value("Customer", hd_bar.name, "hd_customer"),
            hd_bar.name,
        )

    def test_merge_blocked_when_target_has_unrelated_counterpart(self):
        """M1-conflict: merge target's name already exists as unrelated ERP record."""
        enable_erpnext_sync()

        hd_foo, erp_foo = self._make_linked_pair("Merge Block Foo")
        hd_bar = make_hd_customer("Merge Block Bar")
        unrelated_erp = make_erpnext_customer(
            hd_bar.name
        )  # ERP "Merge Block Bar" exists, unrelated

        self.addCleanup(self._safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(self._safe_delete, "Customer", unrelated_erp.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_foo.name)
        self.addCleanup(self._safe_delete, "Customer", erp_foo.name)

        with self.assertRaises(frappe.ValidationError):
            rename_doc(
                doctype="HD Customer",
                old=hd_foo.name,
                new=hd_bar.name,
                merge=True,
                ignore_permissions=True,
            )

        # Nothing changed
        self.assertTrue(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        self.assertTrue(frappe.db.exists("Customer", erp_foo.name))
        self.assertTrue(frappe.db.exists("Customer", unrelated_erp.name))

    def test_merge_cascades_into_existing_counterpart(self):
        """M2: HD Foo+ERP Foo merged into HD Bar+ERP Bar → ERP Foo cascade-merged into ERP Bar."""
        enable_erpnext_sync()

        hd_foo, erp_foo = self._make_linked_pair("M2 Foo", erp_name="M2 Foo ERP")
        hd_bar, erp_bar = self._make_linked_pair("M2 Bar", erp_name="M2 Bar ERP")

        self.addCleanup(self._safe_delete, "Customer", erp_bar.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(self._safe_delete, "Customer", erp_foo.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        # HD Foo and ERP Foo gone; HD Bar and ERP Bar survive
        self.assertFalse(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertFalse(frappe.db.exists("Customer", erp_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        self.assertTrue(frappe.db.exists("Customer", erp_bar.name))
        # Survivors still linked to each other
        self.assertEqual(
            frappe.db.get_value("HD Customer", hd_bar.name, "erpnext_customer"),
            erp_bar.name,
        )
        self.assertEqual(
            frappe.db.get_value("Customer", erp_bar.name, "hd_customer"),
            hd_bar.name,
        )

    def test_merge_no_op_on_other_side_when_old_has_no_counterpart(self):
        """M3: HD Foo (no ERP) merged into HD Bar (has ERP Bar) → ERP side untouched."""
        enable_erpnext_sync()

        hd_foo = make_hd_customer("M3 Foo")
        hd_bar, erp_bar = self._make_linked_pair("M3 Bar")

        self.addCleanup(self._safe_delete, "Customer", erp_bar.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        self.assertFalse(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        # ERP Bar still exists, still linked
        self.assertTrue(frappe.db.exists("Customer", erp_bar.name))
        self.assertEqual(
            frappe.db.get_value("Customer", erp_bar.name, "hd_customer"),
            hd_bar.name,
        )

    def test_rename_no_cascade_when_sync_disabled(self):
        """With sync off, renaming HD Customer should NOT cascade to ERP."""
        # sync is disabled (setUp)

        hd, erp = self._make_linked_pair("Disabled Cascade Old")
        self.addCleanup(self._safe_delete, "HD Customer", "Disabled Cascade New")
        self.addCleanup(self._safe_delete, "Customer", erp.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd.name)

        rename_doc(
            doctype="HD Customer",
            old=hd.name,
            new="Disabled Cascade New",
            ignore_permissions=True,
        )

        # HD renamed
        self.assertTrue(frappe.db.exists("HD Customer", "Disabled Cascade New"))
        # ERP NOT renamed — sync was off
        self.assertTrue(frappe.db.exists("Customer", erp.name))
        self.assertFalse(frappe.db.exists("Customer", "Disabled Cascade New"))

    def test_merge_does_not_cascade_delete_counterpart(self):
        """Regression: merging HD Foo→Bar (both with linked ERPs) must NOT plain-delete ERP Foo;
        it should cascade-merge into ERP Bar instead. ERP Bar must survive with redirected refs.
        """
        enable_erpnext_sync()

        hd_foo, erp_foo = self._make_linked_pair(
            "Regress Foo", erp_name="Regress Foo ERP"
        )
        hd_bar, erp_bar = self._make_linked_pair(
            "Regress Bar", erp_name="Regress Bar ERP"
        )

        self.addCleanup(self._safe_delete, "Customer", erp_bar.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(self._safe_delete, "Customer", erp_foo.name)
        self.addCleanup(self._safe_delete, "HD Customer", hd_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        # ERP Bar must STILL exist after the merge — the bug would have deleted it
        # via on_trash's cascade-delete on HD Foo (which would have found ERP Foo
        # and deleted it, but our concern here is making sure the SURVIVING ERP
        # is intact).
        self.assertTrue(
            frappe.db.exists("Customer", erp_bar.name),
            "ERP Bar (survivor) must not be deleted during HD merge",
        )
        # ERP Foo got merged into ERP Bar
        self.assertFalse(frappe.db.exists("Customer", erp_foo.name))
        # And it was merged (not plain-deleted) — links preserved on ERP Bar
        self.assertEqual(
            frappe.db.get_value("Customer", erp_bar.name, "hd_customer"),
            hd_bar.name,
        )
