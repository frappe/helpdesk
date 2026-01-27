// Copyright (c) 2025, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD View", {
	refresh(frm) {
        if (!frappe.boot.developer_mode){
            if (!frm.doc.is_standard) {
                frm.set_df_property("is_standard", "hidden", 1);
            } else {
                frm.set_df_property("is_standard", "read_only", 1);
                frm.set_df_property("filters", "read_only", 1);
            }
        }
	},
});