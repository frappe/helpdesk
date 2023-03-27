// Copyright (c) 2021, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Article", {
	refresh: function (frm) {
		show_content_wrt_type(frm)

		frm.dashboard.clear_headline()
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
		`)
	},

	content_type: function (frm) {
		show_content_wrt_type(frm)
	},
})

function show_content_wrt_type(frm) {
	frm.toggle_display("content_md", frm.doc.content_type === "Markdown")
	frm.toggle_display("content", frm.doc.content_type === "Rich Text")
}
