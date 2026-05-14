frappe.ui.form.on("Customer", {
  refresh(frm) {
    frm.set_df_property("hd_customer", "hidden", 0);

    if (frm.doc.__islocal) return;
    if (frm.doc.hd_customer) return;

    frm.add_custom_button(
      __("Sync to Helpdesk"),
      () => {
        frappe.call({
          method:
            "helpdesk.helpdesk.integrations.erpnext.customer.sync_erpnext_customer_to_hd",
          args: { customer_name: frm.doc.name },
          freeze: true,
          freeze_message: __("Syncing to Helpdesk..."),
          callback(r) {
            if (r.message?.status === "created") {
              frappe.show_alert({
                message: __("Customer synced to Helpdesk"),
                indicator: "green",
              });
              frm.reload_doc();
            } else if (r.message?.status === "skipped") {
              frappe.show_alert({
                message: __("Already synced with Helpdesk"),
                indicator: "blue",
              });
            }
          },
        });
      },
      __("Actions")
    );
  },
});
