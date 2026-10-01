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

      const { in_sync } = r.message;
      if (in_sync) {
        return;
      }
      const label = "Sync Customers with Helpdesk";

      listview.page.add_menu_item(label, function () {
        frappe.call({
          method: "helpdesk.integrations.erpnext.api.sync_hd_erpnext_customers",
          callback: function () {
            frappe.show_alert({
              message: __("Sync started"),
              indicator: "green",
            });
          },
        });
      });
    },
  });
};
