// Copyright (c) 2023, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Ticket", {
  onload(frm) {
    if (frm.is_new()) return;
    frm.call("mark_seen");
  },
});
