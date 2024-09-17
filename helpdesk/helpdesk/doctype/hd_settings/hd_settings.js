// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Settings", {
  refresh: function (frm) {
    frm.add_custom_button(__("Regenerate Search Index"), () => {
      frappe.call({
        method: "helpdesk.search.build_index",
        callback: function (r) {
          frappe.msgprint(__("Search Index Regenerated"));
        },
      });
    });
  },
});
