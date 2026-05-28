# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.model.rename_doc import rename_doc
from frappe.tests.utils import FrappeTestCase

from helpdesk.integrations.erpnext.api import in_sync, sync_all_customers
from helpdesk.integrations.erpnext.user_permission import sync_user_permissions

from .test_utils import (
    cleanup_user_permission,
    disable_erpnext_sync,
    enable_erpnext_sync,
    link_customers,
    make_doc_share,
    make_erpnext_customer,
    make_hd_customer,
    make_linked_pair,
    make_user_permission,
    make_user_permission_no_sync,
    safe_delete,
)


class TestERPNextIntegration(FrappeTestCase):
    def setUp(self):
        disable_erpnext_sync()

    def tearDown(self):
        disable_erpnext_sync()

    # ------------------------------------------------------------------
    # after_insert
    # ------------------------------------------------------------------

    def test_no_erp_customer_when_sync_disabled(self):
        doc = make_hd_customer("Sync Disabled Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", doc.name, force=True)

        self.assertFalse(frappe.db.exists("Customer", {"hd_customer": doc.name}))

    def test_erp_customer_created_when_sync_enabled(self):
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

    def test_no_duplicate_when_erp_already_linked(self):
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

    def test_image_not_synced_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "Image No Sync")

        hd_doc.image = "/files/new_logo.png"
        hd_doc.save(ignore_permissions=True)

        self.assertNotEqual(
            frappe.db.get_value("Customer", erp_doc.name, "image"),
            "/files/new_logo.png",
        )

    def test_image_syncs_to_erp_customer(self):
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "Image Sync")

        hd_doc.image = "/files/new_logo.png"
        hd_doc.flags.ignore_erpnext_sync = False
        hd_doc.save(ignore_permissions=True)

        self.assertEqual(
            frappe.db.get_value("Customer", erp_doc.name, "image"),
            "/files/new_logo.png",
        )

    # ------------------------------------------------------------------
    # on_trash
    # ------------------------------------------------------------------

    def test_delete_cascades_both_directions(self):
        """Deleting either side cascade-deletes its linked counterpart."""
        enable_erpnext_sync()

        # HD delete → ERP deleted
        hd1, erp1 = link_customers(self, "Cascade Del 1")
        frappe.delete_doc("HD Customer", hd1.name, force=True)
        self.assertFalse(frappe.db.exists("Customer", erp1.name))

        # ERP delete → HD deleted
        hd2, erp2 = link_customers(self, "Cascade Del 2")
        frappe.delete_doc("Customer", erp2.name, force=True)
        self.assertFalse(frappe.db.exists("HD Customer", hd2.name))

    def test_delete_skipped_when_sync_disabled(self):
        """With sync off, deleting either side leaves the counterpart intact."""
        # HD delete: ERP survives
        hd1, erp1 = link_customers(self, "Del No Sync 1")
        frappe.delete_doc("HD Customer", hd1.name, force=True)
        self.assertTrue(frappe.db.exists("Customer", erp1.name))

        # ERP delete: HD survives
        hd2, erp2 = link_customers(self, "Del No Sync 2")
        frappe.delete_doc("Customer", erp2.name, force=True)
        self.assertTrue(frappe.db.exists("HD Customer", hd2.name))

    # ------------------------------------------------------------------
    # User Permission — on_trash mirror cleanup
    # ------------------------------------------------------------------

    def test_user_perm_delete_cascades_both_directions(self):
        """Deleting a perm on either side deletes its mirror on the other."""
        enable_erpnext_sync()

        # HD perm delete → ERP mirror gone
        hd1, erp1 = link_customers(self, "UP Trash 1")
        hd_perm = make_user_permission("Administrator", "HD Customer", hd1.name)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)
        erp_mirror = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp1.name},
        )
        self.assertTrue(erp_mirror)
        frappe.delete_doc("User Permission", hd_perm.name, force=True)
        self.assertFalse(frappe.db.exists("User Permission", erp_mirror))

        # ERP perm delete → HD mirror gone
        hd2, erp2 = link_customers(self, "UP Trash 2")
        erp_perm = make_user_permission("Administrator", "Customer", erp2.name)
        self.addCleanup(frappe.delete_doc, "User Permission", erp_perm.name, force=True)
        hd_mirror = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "HD Customer", "for_value": hd2.name},
        )
        self.assertTrue(hd_mirror)
        frappe.delete_doc("User Permission", erp_perm.name, force=True)
        self.assertFalse(frappe.db.exists("User Permission", hd_mirror))

    def test_user_perm_delete_skipped_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "UP Trash Disabled")

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
    # DocShare — on_trash mirror cleanup
    # ------------------------------------------------------------------

    def test_doc_share_delete_cascades_both_directions(self):
        """Deleting a share on either side deletes its mirror on the other."""
        enable_erpnext_sync()

        # HD share delete → ERP mirror gone
        hd1, erp1 = link_customers(self, "DS Trash 1")
        hd_share = make_doc_share("HD Customer", hd1.name)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)
        erp_mirror = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp1.name,
            },
        )
        self.assertTrue(erp_mirror)
        frappe.delete_doc("DocShare", hd_share.name, force=True)
        self.assertFalse(frappe.db.exists("DocShare", erp_mirror))

        # ERP share delete → HD mirror gone
        hd2, erp2 = link_customers(self, "DS Trash 2")
        erp_share = make_doc_share("Customer", erp2.name)
        self.addCleanup(frappe.delete_doc, "DocShare", erp_share.name, force=True)
        hd_mirror = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd2.name,
            },
        )
        self.assertTrue(hd_mirror)
        frappe.delete_doc("DocShare", erp_share.name, force=True)
        self.assertFalse(frappe.db.exists("DocShare", hd_mirror))

    def test_doc_share_delete_skipped_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "DS Trash Disabled")

        erp_share = make_doc_share("Customer", erp_doc.name, ignore_erpnext_sync=True)
        hd_share = make_doc_share("HD Customer", hd_doc.name, ignore_erpnext_sync=True)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        frappe.delete_doc("DocShare", erp_share.name, force=True)

        self.assertTrue(frappe.db.exists("DocShare", hd_share.name))

    # ------------------------------------------------------------------
    # DocShare — insert/update mirroring
    # ------------------------------------------------------------------

    def test_doc_share_mirrors_both_directions(self):
        """Creating a DocShare on either side creates a mirror on the other with the same perms."""
        enable_erpnext_sync()

        # HD share → ERP mirror (with non-default perms to verify state carryover)
        hd1, erp1 = link_customers(self, "DS Mirror 1")
        share1 = make_doc_share("HD Customer", hd1.name, write=1)
        self.addCleanup(frappe.delete_doc, "DocShare", share1.name, force=True)
        mirror1 = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp1.name,
            },
            ["name", "read", "write"],
            as_dict=True,
        )
        self.assertTrue(mirror1)
        self.addCleanup(frappe.delete_doc, "DocShare", mirror1.name, force=True)
        self.assertEqual((mirror1.read, mirror1.write), (1, 1))

        # ERP share → HD mirror
        hd2, erp2 = link_customers(self, "DS Mirror 2")
        share2 = make_doc_share("Customer", erp2.name, share=1)
        self.addCleanup(frappe.delete_doc, "DocShare", share2.name, force=True)
        self.assertTrue(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "HD Customer",
                    "share_name": hd2.name,
                },
            )
        )

    def test_doc_share_not_mirrored_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "DS Disabled")

        share = make_doc_share("Customer", erp_doc.name)
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

    def test_doc_share_not_duplicated_if_mirror_exists(self):
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "DS No Dup")

        existing = make_doc_share("Customer", erp_doc.name, ignore_erpnext_sync=True)
        self.addCleanup(frappe.delete_doc, "DocShare", existing.name, force=True)

        share = make_doc_share("HD Customer", hd_doc.name)
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

    def test_doc_share_not_mirrored_when_unlinked(self):
        enable_erpnext_sync()

        hd_doc = make_hd_customer("DS Unlinked HD Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        share = make_doc_share("HD Customer", hd_doc.name)
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

    def test_doc_share_update_syncs_to_mirror(self):
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "DS Update")

        hd_share = make_doc_share("HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
            },
        )
        self.addCleanup(frappe.delete_doc, "DocShare", mirror_name, force=True)
        self.assertEqual(frappe.db.get_value("DocShare", mirror_name, "write"), 0)

        hd_share.write = 1
        hd_share.flags.ignore_share_permission = True
        hd_share.save(ignore_permissions=True)

        self.assertEqual(frappe.db.get_value("DocShare", mirror_name, "write"), 1)

    def test_doc_share_update_skipped_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "DS Update Disabled")

        hd_share = make_doc_share("HD Customer", hd_doc.name, ignore_erpnext_sync=True)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        erp_share = make_doc_share("Customer", erp_doc.name, ignore_erpnext_sync=True)
        self.addCleanup(frappe.delete_doc, "DocShare", erp_share.name, force=True)

        hd_share.write = 1
        hd_share.flags.ignore_share_permission = True
        hd_share.save(ignore_permissions=True)

        self.assertEqual(frappe.db.get_value("DocShare", erp_share.name, "write"), 0)

    # ------------------------------------------------------------------
    # DocShare — identity-change handling (on_update)
    # ------------------------------------------------------------------

    def test_doc_share_name_change_recreates_mirror(self):
        """Changing share_name should delete the old mirror and create a new one."""
        enable_erpnext_sync()

        hd_a, erp_a = link_customers(self, "DS Identity A")
        hd_c, erp_c = link_customers(self, "DS Identity C")

        hd_share = make_doc_share("HD Customer", hd_a.name)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        old_mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_a.name,
            },
        )
        self.assertTrue(old_mirror_name)

        hd_share.share_name = hd_c.name
        hd_share.flags.ignore_share_permission = True
        hd_share.save(ignore_permissions=True)

        self.assertFalse(frappe.db.exists("DocShare", old_mirror_name))
        new_mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_c.name,
            },
        )
        self.assertTrue(new_mirror_name)
        self.addCleanup(frappe.delete_doc, "DocShare", new_mirror_name, force=True)

    def test_doc_share_doctype_change_flips_mirror(self):
        """Flipping share_doctype HD→Customer should delete the old mirror and create one on the opposite side."""
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "DS Flip")

        hd_share = make_doc_share("HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        old_mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
            },
        )
        self.assertTrue(old_mirror_name)

        hd_share.share_doctype = "Customer"
        hd_share.share_name = erp_doc.name
        hd_share.flags.ignore_share_permission = True
        hd_share.save(ignore_permissions=True)

        new_mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "HD Customer",
                "share_name": hd_doc.name,
            },
        )
        self.assertTrue(new_mirror_name)
        self.assertNotEqual(new_mirror_name, hd_share.name)
        self.addCleanup(frappe.delete_doc, "DocShare", new_mirror_name, force=True)

    def test_doc_share_change_to_unlinked_deletes_mirror(self):
        """Changing share_name to an unlinked record should delete the old mirror and create no new mirror."""
        enable_erpnext_sync()
        hd_linked, erp_doc = link_customers(self, "DS Unlink Linked")
        hd_orphan = make_hd_customer("DS Unlink HD Orphan")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_orphan.name, force=True)

        hd_share = make_doc_share("HD Customer", hd_linked.name)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)

        old_mirror_name = frappe.db.get_value(
            "DocShare",
            {
                "user": "Administrator",
                "share_doctype": "Customer",
                "share_name": erp_doc.name,
            },
        )
        self.assertTrue(old_mirror_name)

        hd_share.share_name = hd_orphan.name
        hd_share.flags.ignore_share_permission = True
        hd_share.save(ignore_permissions=True)

        self.assertFalse(frappe.db.exists("DocShare", old_mirror_name))
        self.assertFalse(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "Customer",
                    "share_name": hd_orphan.name,
                },
            )
        )

    def test_mirror_cleanup_survives_repointed_forward_link(self):
        """If the source's forward link is re-pointed but the back-link still
        points at us, identity-change cleanup must find the ORIGINAL mirror via
        the back-link — not the unrelated mirror at the new forward target.
        Regression test for the bug where _find_target_for used the forward link."""
        enable_erpnext_sync()
        hd, erp_orig = link_customers(self, "DS Repoint Orig")
        _, erp_new = link_customers(self, "DS Repoint New")
        hd_orphan = make_hd_customer("DS Repoint Orphan")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_orphan.name, force=True)

        # Share HD → creates mirror at erp_orig (back-link erp_orig.hd_customer=hd)
        hd_share = make_doc_share("HD Customer", hd.name)
        self.addCleanup(frappe.delete_doc, "DocShare", hd_share.name, force=True)
        self.assertTrue(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "Customer",
                    "share_name": erp_orig.name,
                },
            )
        )

        # Admin re-points only the forward link (leaves erp_orig.hd_customer alone)
        frappe.db.set_value(
            "HD Customer",
            hd.name,
            "erpnext_customer",
            erp_new.name,
            update_modified=False,
        )

        # Identity change on the share triggers cleanup
        hd_share.share_name = hd_orphan.name
        hd_share.flags.ignore_share_permission = True
        hd_share.save(ignore_permissions=True)

        # Original mirror at erp_orig must be deleted — and the unrelated
        # mirror at erp_new (which doesn't exist; we never shared with it)
        # must not be confused for it.
        self.assertFalse(
            frappe.db.exists(
                "DocShare",
                {
                    "user": "Administrator",
                    "share_doctype": "Customer",
                    "share_name": erp_orig.name,
                },
            )
        )

    # ------------------------------------------------------------------
    # User Permission — insert/update mirroring
    # ------------------------------------------------------------------

    def test_perm_mirrors_both_directions(self):
        """Creating a User Permission on either side creates a mirror on the other."""
        enable_erpnext_sync()

        # HD perm → ERP mirror
        hd1, erp1 = link_customers(self, "UP Mirror 1")
        perm1 = make_user_permission("Administrator", "HD Customer", hd1.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm1.name, force=True)
        self.addCleanup(cleanup_user_permission, "Administrator", "Customer", erp1.name)
        self.assertTrue(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": erp1.name,
                },
            )
        )

        # ERP perm → HD mirror
        hd2, erp2 = link_customers(self, "UP Mirror 2")
        perm2 = make_user_permission("Administrator", "Customer", erp2.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm2.name, force=True)
        self.addCleanup(
            cleanup_user_permission, "Administrator", "HD Customer", hd2.name
        )
        self.assertTrue(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "HD Customer",
                    "for_value": hd2.name,
                },
            )
        )

    def test_perm_not_mirrored_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "UP Disabled")

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

    def test_perm_not_duplicated_if_mirror_exists(self):
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "UP No Dup")

        existing_mirror = make_user_permission_no_sync(
            "Administrator", "Customer", erp_doc.name
        )
        self.addCleanup(
            frappe.delete_doc, "User Permission", existing_mirror.name, force=True
        )

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

    def test_perm_mirror_dedup_respects_applicable_for(self):
        """Dedup must match Frappe's 5-key duplicate validation: a Customer-side
        perm with different `applicable_for` is NOT a duplicate of our incoming
        mirror, so we must still insert. Old 3-key dedup would skip-and-leak."""
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "UP Applicable Dedup")

        # Pre-existing Customer-side perm narrowed to a specific applicable_for
        # (apply_to_all_doctypes=0 is required when applicable_for is set).
        existing = make_user_permission_no_sync(
            "Administrator",
            "Customer",
            erp_doc.name,
            apply_to_all_doctypes=0,
            applicable_for="Sales Invoice",
        )
        self.addCleanup(frappe.delete_doc, "User Permission", existing.name, force=True)

        # New HD perm with apply_to_all_doctypes=1 (no applicable_for) — distinct
        # from `existing` on Frappe's duplicate key, so a mirror must be created.
        hd_perm = make_user_permission(
            "Administrator", "HD Customer", hd_doc.name, apply_to_all_doctypes=1
        )
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        # Two Customer-side perms must coexist: the pre-existing narrowed one
        # and the freshly-created mirror for the HD perm.
        customer_perms = frappe.get_all(
            "User Permission",
            filters={
                "user": "Administrator",
                "allow": "Customer",
                "for_value": erp_doc.name,
            },
            fields=["name", "applicable_for", "apply_to_all_doctypes"],
        )
        self.assertEqual(len(customer_perms), 2)
        for p in customer_perms:
            if p.name != existing.name:
                self.addCleanup(
                    frappe.delete_doc, "User Permission", p.name, force=True
                )

    def test_perm_not_mirrored_when_unlinked(self):
        enable_erpnext_sync()

        hd_doc = make_hd_customer("UP Unlinked HD Co")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_doc.name, force=True)

        perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)

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

    def test_user_perm_update_syncs_to_mirror(self):
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "UP Update")

        hd_perm = make_user_permission(
            "Administrator", "HD Customer", hd_doc.name, apply_to_all_doctypes=1
        )
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp_doc.name},
        )
        self.addCleanup(frappe.delete_doc, "User Permission", mirror_name, force=True)
        self.assertEqual(
            frappe.db.get_value(
                "User Permission", mirror_name, "apply_to_all_doctypes"
            ),
            1,
        )

        hd_perm.apply_to_all_doctypes = 0
        hd_perm.save(ignore_permissions=True)

        self.assertEqual(
            frappe.db.get_value(
                "User Permission", mirror_name, "apply_to_all_doctypes"
            ),
            0,
        )

    def test_user_perm_update_skipped_when_sync_disabled(self):
        hd_doc, erp_doc = link_customers(self, "UP Update Disabled")

        hd_perm = make_user_permission_no_sync(
            "Administrator", "HD Customer", hd_doc.name, apply_to_all_doctypes=1
        )
        erp_perm = make_user_permission_no_sync(
            "Administrator", "Customer", erp_doc.name, apply_to_all_doctypes=1
        )
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)
        self.addCleanup(frappe.delete_doc, "User Permission", erp_perm.name, force=True)

        hd_perm.apply_to_all_doctypes = 0
        hd_perm.save(ignore_permissions=True)

        self.assertEqual(
            frappe.db.get_value(
                "User Permission", erp_perm.name, "apply_to_all_doctypes"
            ),
            1,
        )

    # ------------------------------------------------------------------
    # User Permission — identity-change handling (on_update)
    # ------------------------------------------------------------------

    def test_user_perm_for_value_change_recreates_mirror(self):
        """Changing for_value to another linked HD Customer should delete the old
        ERP mirror and create one at the new linked ERP Customer."""
        enable_erpnext_sync()

        hd_a, erp_a = link_customers(self, "UP Identity A")
        hd_c, erp_c = link_customers(self, "UP Identity C")

        hd_perm = make_user_permission("Administrator", "HD Customer", hd_a.name)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        old_mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp_a.name},
        )
        self.assertTrue(old_mirror_name)

        hd_perm.for_value = hd_c.name
        hd_perm.save(ignore_permissions=True)

        self.assertFalse(frappe.db.exists("User Permission", old_mirror_name))
        new_mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp_c.name},
        )
        self.assertTrue(new_mirror_name)
        self.addCleanup(
            frappe.delete_doc, "User Permission", new_mirror_name, force=True
        )

    def test_user_perm_allow_change_flips_mirror(self):
        """Flipping allow HD→Customer should delete the old mirror on Customer side
        and create a new one on HD Customer side."""
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "UP Flip")

        hd_perm = make_user_permission("Administrator", "HD Customer", hd_doc.name)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        old_mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp_doc.name},
        )
        self.assertTrue(old_mirror_name)

        hd_perm.allow = "Customer"
        hd_perm.for_value = erp_doc.name
        hd_perm.save(ignore_permissions=True)

        new_mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "HD Customer", "for_value": hd_doc.name},
        )
        self.assertTrue(new_mirror_name)
        self.assertNotEqual(new_mirror_name, hd_perm.name)
        self.addCleanup(
            frappe.delete_doc, "User Permission", new_mirror_name, force=True
        )

    def test_user_perm_change_to_unlinked_deletes_mirror(self):
        """Changing for_value to an unlinked HD Customer should delete the old mirror
        and create no new mirror."""
        enable_erpnext_sync()
        hd_linked, erp_doc = link_customers(self, "UP Unlink Linked")
        hd_orphan = make_hd_customer("UP Unlink HD Orphan")
        self.addCleanup(frappe.delete_doc, "HD Customer", hd_orphan.name, force=True)

        hd_perm = make_user_permission("Administrator", "HD Customer", hd_linked.name)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        old_mirror_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "Customer", "for_value": erp_doc.name},
        )
        self.assertTrue(old_mirror_name)

        hd_perm.for_value = hd_orphan.name
        hd_perm.save(ignore_permissions=True)

        self.assertFalse(frappe.db.exists("User Permission", old_mirror_name))
        self.assertFalse(
            frappe.db.exists(
                "User Permission",
                {
                    "user": "Administrator",
                    "allow": "Customer",
                    "for_value": hd_orphan.name,
                },
            )
        )

    # ------------------------------------------------------------------
    # User Permission — bulk sync (sync_user_permissions)
    # ------------------------------------------------------------------

    def test_bulk_sync_is_idempotent(self):
        """Calling sync_user_permissions when mirrors already exist is a no-op."""
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "UP Bulk Dup")

        erp_perm = make_user_permission_no_sync(
            "Administrator", "Customer", erp_doc.name
        )
        hd_perm = make_user_permission_no_sync(
            "Administrator", "HD Customer", hd_doc.name
        )
        self.addCleanup(frappe.delete_doc, "User Permission", erp_perm.name, force=True)
        self.addCleanup(frappe.delete_doc, "User Permission", hd_perm.name, force=True)

        sync_user_permissions()

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

    def test_in_sync_reflects_link_state(self):
        """Pre-sync (unlinked records on either side) → False; after running
        sync_all_customers (which links by name and creates missing counterparts)
        → True. Covers the initial-sync case where both sides have records but
        none are linked — the scenario the old inverted logic miscalled as True."""
        enable_erpnext_sync()

        hd = make_hd_customer("InSync HD Only")
        erp = make_erpnext_customer("InSync ERP Only")
        # Sync creates the missing counterpart on the other side for each, so
        # register cleanup for both names on both doctypes.
        self.addCleanup(safe_delete, "HD Customer", hd.name)
        self.addCleanup(safe_delete, "Customer", hd.name)
        self.addCleanup(safe_delete, "Customer", erp.name)
        self.addCleanup(safe_delete, "HD Customer", erp.name)

        self.assertFalse(in_sync())

        sync_all_customers()

        self.assertTrue(in_sync())

    def test_apply_to_all_doctypes_preserved(self):
        """The apply_to_all_doctypes flag should be carried over to the mirror."""
        enable_erpnext_sync()
        hd_doc, erp_doc = link_customers(self, "UP Flag")

        perm = make_user_permission(
            "Administrator", "Customer", erp_doc.name, apply_to_all_doctypes=0
        )
        self.addCleanup(frappe.delete_doc, "User Permission", perm.name, force=True)
        self.addCleanup(
            cleanup_user_permission, "Administrator", "HD Customer", hd_doc.name
        )

        mirrored_name = frappe.db.get_value(
            "User Permission",
            {"user": "Administrator", "allow": "HD Customer", "for_value": hd_doc.name},
            "name",
        )
        self.assertTrue(mirrored_name)
        self.assertEqual(
            frappe.db.get_value(
                "User Permission", mirrored_name, "apply_to_all_doctypes"
            ),
            0,
        )

    # ------------------------------------------------------------------
    # Rename cascade (plain + merge)
    # ------------------------------------------------------------------

    def test_plain_rename_cascades_both_directions(self):
        """Renaming either side cascade-renames the linked counterpart."""
        enable_erpnext_sync()

        # HD rename → ERP renamed
        hd1, erp1 = make_linked_pair("Cascade HD Old")
        self.addCleanup(safe_delete, "HD Customer", "Cascade HD New")
        self.addCleanup(safe_delete, "Customer", "Cascade HD New")
        self.addCleanup(safe_delete, "HD Customer", hd1.name)
        self.addCleanup(safe_delete, "Customer", erp1.name)
        rename_doc(
            doctype="HD Customer",
            old=hd1.name,
            new="Cascade HD New",
            ignore_permissions=True,
        )
        self.assertTrue(frappe.db.exists("Customer", "Cascade HD New"))
        self.assertFalse(frappe.db.exists("Customer", erp1.name))
        self.assertEqual(
            frappe.db.get_value("HD Customer", "Cascade HD New", "erpnext_customer"),
            "Cascade HD New",
        )
        self.assertEqual(
            frappe.db.get_value("Customer", "Cascade HD New", "hd_customer"),
            "Cascade HD New",
        )

        # ERP rename → HD renamed
        hd2, erp2 = make_linked_pair("Cascade ERP Old")
        self.addCleanup(safe_delete, "HD Customer", "Cascade ERP New")
        self.addCleanup(safe_delete, "Customer", "Cascade ERP New")
        self.addCleanup(safe_delete, "HD Customer", hd2.name)
        self.addCleanup(safe_delete, "Customer", erp2.name)
        rename_doc(
            doctype="Customer",
            old=erp2.name,
            new="Cascade ERP New",
            ignore_permissions=True,
        )
        self.assertTrue(frappe.db.exists("HD Customer", "Cascade ERP New"))
        self.assertEqual(
            frappe.db.get_value("HD Customer", "Cascade ERP New", "erpnext_customer"),
            "Cascade ERP New",
        )

    def test_plain_rename_no_cascade_when_no_counterpart(self):
        enable_erpnext_sync()

        hd = make_hd_customer("Lonely HD Old")
        self.addCleanup(safe_delete, "HD Customer", "Lonely HD New")
        self.addCleanup(safe_delete, "HD Customer", hd.name)

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

        hd, erp = make_linked_pair("Conflict HD Old")
        unrelated_erp = make_erpnext_customer("Conflict HD New")
        self.addCleanup(safe_delete, "HD Customer", hd.name)
        self.addCleanup(safe_delete, "Customer", erp.name)
        self.addCleanup(safe_delete, "Customer", unrelated_erp.name)

        with self.assertRaises(frappe.ValidationError):
            rename_doc(
                doctype="HD Customer",
                old=hd.name,
                new="Conflict HD New",
                ignore_permissions=True,
            )

        self.assertTrue(frappe.db.exists("HD Customer", hd.name))
        self.assertTrue(frappe.db.exists("Customer", erp.name))
        self.assertTrue(frappe.db.exists("Customer", unrelated_erp.name))

    def test_merge_transfers_when_target_has_no_counterpart(self):
        """M1: HD Foo (has ERP) merged into HD Bar (no ERP) → ERP Foo transferred to Bar."""
        enable_erpnext_sync()

        hd_foo, erp_foo = make_linked_pair("Merge M1 Foo")
        hd_bar = make_hd_customer("Merge M1 Bar")

        self.addCleanup(safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(safe_delete, "Customer", hd_bar.name)
        self.addCleanup(safe_delete, "HD Customer", hd_foo.name)
        self.addCleanup(safe_delete, "Customer", erp_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        self.assertFalse(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        self.assertFalse(frappe.db.exists("Customer", erp_foo.name))
        self.assertTrue(frappe.db.exists("Customer", hd_bar.name))
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

        hd_foo, erp_foo = make_linked_pair("Merge Block Foo")
        hd_bar = make_hd_customer("Merge Block Bar")
        unrelated_erp = make_erpnext_customer(hd_bar.name)

        self.addCleanup(safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(safe_delete, "Customer", unrelated_erp.name)
        self.addCleanup(safe_delete, "HD Customer", hd_foo.name)
        self.addCleanup(safe_delete, "Customer", erp_foo.name)

        with self.assertRaises(frappe.ValidationError):
            rename_doc(
                doctype="HD Customer",
                old=hd_foo.name,
                new=hd_bar.name,
                merge=True,
                ignore_permissions=True,
            )

        self.assertTrue(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        self.assertTrue(frappe.db.exists("Customer", erp_foo.name))
        self.assertTrue(frappe.db.exists("Customer", unrelated_erp.name))

    def test_merge_cascades_into_existing_counterpart(self):
        """M2: HD Foo+ERP Foo merged into HD Bar+ERP Bar → ERP Foo cascade-merged into ERP Bar."""
        enable_erpnext_sync()

        hd_foo, erp_foo = make_linked_pair("M2 Foo", erp_name="M2 Foo ERP")
        hd_bar, erp_bar = make_linked_pair("M2 Bar", erp_name="M2 Bar ERP")

        self.addCleanup(safe_delete, "Customer", erp_bar.name)
        self.addCleanup(safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(safe_delete, "Customer", erp_foo.name)
        self.addCleanup(safe_delete, "HD Customer", hd_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        self.assertFalse(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertFalse(frappe.db.exists("Customer", erp_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        self.assertTrue(frappe.db.exists("Customer", erp_bar.name))
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
        hd_bar, erp_bar = make_linked_pair("M3 Bar")

        self.addCleanup(safe_delete, "Customer", erp_bar.name)
        self.addCleanup(safe_delete, "HD Customer", hd_bar.name)
        self.addCleanup(safe_delete, "HD Customer", hd_foo.name)

        rename_doc(
            doctype="HD Customer",
            old=hd_foo.name,
            new=hd_bar.name,
            merge=True,
            ignore_permissions=True,
        )

        self.assertFalse(frappe.db.exists("HD Customer", hd_foo.name))
        self.assertTrue(frappe.db.exists("HD Customer", hd_bar.name))
        self.assertTrue(frappe.db.exists("Customer", erp_bar.name))
        self.assertEqual(
            frappe.db.get_value("Customer", erp_bar.name, "hd_customer"),
            hd_bar.name,
        )

    def test_rename_no_cascade_when_sync_disabled(self):
        hd, erp = make_linked_pair("Disabled Cascade Old")
        self.addCleanup(safe_delete, "HD Customer", "Disabled Cascade New")
        self.addCleanup(safe_delete, "Customer", erp.name)
        self.addCleanup(safe_delete, "HD Customer", hd.name)

        rename_doc(
            doctype="HD Customer",
            old=hd.name,
            new="Disabled Cascade New",
            ignore_permissions=True,
        )

        self.assertTrue(frappe.db.exists("HD Customer", "Disabled Cascade New"))
        self.assertTrue(frappe.db.exists("Customer", erp.name))
        self.assertFalse(frappe.db.exists("Customer", "Disabled Cascade New"))
