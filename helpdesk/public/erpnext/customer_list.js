frappe.listview_settings["Customer"] =
  frappe.listview_settings["Customer"] || {};

const _original_onload = frappe.listview_settings["Customer"].onload;

frappe.listview_settings["Customer"].onload = function (listview) {
  if (_original_onload) {
    _original_onload(listview);
  }

  const is_erp_installed = frappe.boot.app_data.filter(
    (app) => app.app_name === "erpnext"
  ).length;
  if (!is_erp_installed) {
    return;
  }

  frappe.call({
    method: "helpdesk.integrations.erpnext.api.get_sync_info",
    callback: function (r) {
      if (!r.message || !r.message.enabled) {
        return;
      }

      const { hd_count, erp_count, in_sync } = r.message;
      if (in_sync) {
        return;
      }
      const label = "Sync Customers with Helpdesk";

      listview.page.add_menu_item(label, function () {
        frappe.call({
          method: "helpdesk.integrations.erpnext.api.sync_hd_erpnext_customers",
          freeze: true,
          freeze_message: "Syncing customers with Helpdesk...",
          callback: function () {
            listview.refresh();
            frappe.show_alert({
              message: "Customers synced with Helpdesk successfully",
              indicator: "green",
            });
          },
        });
      });
    },
  });
};
