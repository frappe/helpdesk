# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketStatus(Document):
    def before_rename(self, old, new, merge=False):
        if old == "Closed":
            frappe.throw(_("The 'Closed' status cannot be renamed."))

    def validate(self):
        self.validate_closed_status_change()
        self.validate_required_categories()
        self.validate_disabling_status()

    def validate_closed_status_change(self):
        if self.is_new():
            return
        old_name = (
            self.get_doc_before_save().name if self.get_doc_before_save() else None
        )
        if old_name == "Closed" and not (
            self.has_value_changed("order") or self.has_value_changed("color")
        ):
            frappe.throw(
                _(
                    "Only the 'color' and 'order' fields of the 'Closed' status can be modified."
                )
            )

    def validate_required_categories(self):
        if self.is_new():
            return
        if not self.has_value_changed("category"):
            return
        old_category = (
            self.get_doc_before_save().category if self.get_doc_before_save() else None
        )

        if not old_category:
            return

        # If category is being changed, check if we're removing the last status of a required category
        if old_category != self.category:
            count = frappe.db.count(
                "HD Ticket Status",
                {"category": old_category, "name": ["!=", self.name]},
            )

            if count == 0:
                frappe.throw(
                    _(
                        f"At least one ticket status with category '{old_category}' must exist in the system."
                    )
                )

    def validate_disabling_status(self):
        if self.is_new() or self.enabled:
            return
        count = frappe.db.count(
            "HD Ticket Status",
            {
                "enabled": 1,
                "name": ["not in", [self.name, "Closed"]],
                "category": self.category,
            },
        )
        if count == 0:
            frappe.throw(
                _(
                    "At least one enabled status for <u>{0}</u> category must be enabled."
                ).format(self.category)
            )

        # check in HD Service Level Agreement if this status is used as default or reopen status
        sla_default_status = frappe.db.exists(
            "HD Service Level Agreement",
            {"default_ticket_status": self.name},
        )
        sla_reopen_status = frappe.db.exists(
            "HD Service Level Agreement",
            {"ticket_reopen_status": self.name},
        )
        if sla_default_status or sla_reopen_status:
            message = _(
                "Cannot disable this status as it is linked in the following SLAs:<br><br>"
            )
            if sla_default_status:
                message += _("- {0} as Default Status<br>").format(sla_default_status)
            if sla_reopen_status:
                message += _("- {0} as Reopen Status<br>").format(sla_reopen_status)
            message += _(
                "<br>Please update the SLA(s) to use a different status before disabling this status."
            )
            frappe.throw(message)

        # check in HD Settings if this status is used as default or reopen status
        settings_default_status = frappe.db.get_single_value(
            "HD Settings", "default_ticket_status"
        )

        settings_reopen_status = frappe.db.get_single_value(
            "HD Settings", "ticket_reopen_status"
        )

        if self.name in [settings_default_status, settings_reopen_status]:
            message = _(
                "Cannot disable this status as it is linked in HD Settings:<br><br>"
            )
            if self.name == settings_default_status:
                message += _("- Default Ticket Status<br>")
            if self.name == settings_reopen_status:
                message += _("- Ticket Reopen Status<br>")
            message += _(
                "<br>Please update HD Settings to use a different status before disabling this status."
            )
            frappe.throw(message)
