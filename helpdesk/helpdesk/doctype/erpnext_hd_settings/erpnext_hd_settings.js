// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("ERPNext HD Settings", {
  refresh(frm) {
    if (!frm.doc.enabled) {
      return;
    }

    frappe.call({
      method: "helpdesk.integrations.erpnext.api.get_sync_info",
      callback: function (r) {
        if (!r.message || !r.message.enabled || r.message.in_sync) {
          return;
        }
        frm.add_custom_button(__("Sync Customers with Helpdesk"), function () {
          frappe.call({
            method:
              "helpdesk.integrations.erpnext.api.sync_hd_erpnext_customers",
            freeze: true,
            freeze_message: __("Syncing customers with Helpdesk..."),
            callback: function () {
              frappe.show_alert({
                message: __("Customers synced with Helpdesk successfully"),
                indicator: "green",
              });
            },
          });
        });
      },
    });
  },
});
