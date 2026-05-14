frappe.listview_settings["Customer"] =
  frappe.listview_settings["Customer"] || {};

Object.assign(frappe.listview_settings["Customer"], {
  onload(listview) {
    listview.page.add_action_item(__("Sync to Helpdesk"), () => {
      const selected = listview.get_checked_items();
      if (!selected.length) {
        frappe.msgprint(__("Please select at least one customer."));
        return;
      }

      frappe.call({
        method:
          "helpdesk.helpdesk.integrations.erpnext.customer.bulk_sync_erpnext_customers_to_hd",
        args: { customer_names: selected.map((c) => c.name) },
        freeze: true,
        freeze_message: __("Syncing to Helpdesk..."),
        callback(r) {
          if (r.message) {
            const { created, skipped } = r.message;
            frappe.show_alert({
              message: __("{0} created, {1} already synced", [
                created,
                skipped,
              ]),
              indicator: "green",
            });
            listview.refresh();
          }
        },
      });
    });
  },
});
