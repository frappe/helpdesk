// Copyright (c) 2022, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('HD Agent', {
    refresh: function(frm) {
        // Example: make status editable
        frm.set_df_property('availability_status', 'read_only', 0);
    }
});
