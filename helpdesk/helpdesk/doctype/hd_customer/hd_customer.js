// Copyright (c) 2022, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Customer", {
  // if erpnext is not installed on the site hide the field "erp_customer"
  // TODO: hide field
  refresh: function (frm) {
    // if (!frappe.modules.erpnext) {
    // frm.set_df_property("erp_customer", "hidden", true);
    // }
  },
});
