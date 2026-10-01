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
        frm.add_custom_button(__("Sync Customers"), function () {
          const dialog = new frappe.ui.Dialog({
            title: __("Sync Customers"),
            fields: [
              {
                fieldtype: "HTML",
                options: `<p class="text-muted">${__(
                  "Sync all customers between ERPNext and Helpdesk? The sync runs in the background and can take a few minutes depending on the number of customers."
                )}</p>`,
              },
            ],
            primary_action_label: __("Confirm"),
            primary_action() {
              dialog.hide();
              frappe.call({
                method:
                  "helpdesk.integrations.erpnext.api.sync_hd_erpnext_customers",
                callback: function () {
                  frappe.show_alert({
                    message: __("Sync started"),
                    indicator: "green",
                  });
                },
              });
            },
          });
          dialog.show();
        });
      },
    });
  },
});
