// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('HD Canned Response', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Preview'), function() {
				frappe.msgprint({
					title: __('Message Preview'),
					message: frm.doc.message,
					indicator: 'blue'
				});
			});

			if (frm.doc.usage_count > 0) {
				frm.dashboard.add_indicator(__('Used {0} times', [frm.doc.usage_count]), 'blue');
			}
		}

		// Add help text for shortcuts
		frm.set_df_property('shortcut', 'description',
			__('Type this shortcut (e.g., /thanks) in the comment box to quickly insert this response'));
	},

	shortcut: function(frm) {
		// Auto-format shortcut
		if (frm.doc.shortcut && !frm.doc.shortcut.startsWith('/')) {
			frm.set_value('shortcut', '/' + frm.doc.shortcut);
		}
	}
});
