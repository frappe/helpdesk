// Copyright (c) 2021, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Article', {
	refresh: function(frm) {
		frm.dashboard.clear_headline();

		frm.dashboard.set_headline_alert(`
			<div class="row">
				<div class="col-md-4 col-xs-12">
					<span class="indicator whitespace-nowrap red">
						<span>Views: ${frm.doc.views || 0}</span>
					</span>
				</div>
				<div class="col-md-4 col-xs-12">
					<span class="indicator whitespace-nowrap green">
						<span>Helpful: ${frm.doc.helpful || 0}</span>
					</span>
				</div>
				<div class="col-md-4 col-xs-12">
					<span class="indicator whitespace-nowrap red">
						<span>Not Helpful: ${frm.doc.not_helpful || 0}</span>
					</span>
				</div>
			</div>
		`);
	}
});
