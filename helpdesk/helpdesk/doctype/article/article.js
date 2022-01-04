// Copyright (c) 2021, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Article', {
	refresh: function(frm) {
		if(frm.doc.linked_web_page && frm.doc.published) {
			frm.add_custom_button(
				'Open Web Page',
				() => {
					window.open(`/${frm.doc.route}`)
				}
			);
		}
	}
});
