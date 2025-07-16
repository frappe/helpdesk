// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Form Script", {
  refresh(frm) {
    if (frm.doc.is_standard && !frappe.boot.developer_mode) {
      frm.disable_form();
      frappe.show_alert(
        __(
          "Standard Form Scripts can't be modified, duplicate the script instead."
        )
      );
    }
  },
});
