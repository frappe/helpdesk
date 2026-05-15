import frappe

SCRIPT_NAME = "HD - Sync Customers with Helpdesk"

CLIENT_SCRIPT = """
frappe.listview_settings["Customer"] = frappe.listview_settings["Customer"] || {};

const _original_onload = frappe.listview_settings["Customer"].onload;

frappe.listview_settings["Customer"].onload = function (listview) {
    if (_original_onload) {
        _original_onload(listview);
    }

    if (!frappe.boot.installed_apps.includes("helpdesk")) {
        return;
    }

    frappe.call({
        method: "helpdesk.integrations.erpnext.customer.get_sync_info",
        callback: function (r) {
            if (!r.message || !r.message.enabled) {
                return;
            }

            const { hd_count, erp_count, in_sync } = r.message;
            const label = in_sync
                ? "Sync with HD"
                : `Sync with HD (${Math.abs(erp_count - hd_count)} unsynced)`;

            listview.page.menu_item(label, function () {
                frappe.call({
                    method: "helpdesk.integrations.erpnext.customer.sync_hd_erpnext_customers",
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
"""


def execute():
    if "erpnext" not in frappe.get_installed_apps():
        return

    if frappe.db.exists("Client Script", SCRIPT_NAME):
        frappe.db.set_value("Client Script", SCRIPT_NAME, "script", CLIENT_SCRIPT)
        frappe.db.set_value("Client Script", SCRIPT_NAME, "enabled", 1)
        return

    frappe.get_doc(
        {
            "doctype": "Client Script",
            "name": SCRIPT_NAME,
            "dt": "Customer",
            "view": "List",
            "enabled": 1,
            "script": CLIENT_SCRIPT,
        }
    ).insert(ignore_permissions=True)
