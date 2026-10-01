// Copyright (c) 2026, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

frappe.ui.form.on("HDS Support Connection", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.connection_status !== "Connected") {
			frm.add_custom_button(__("Register Client"), function () {
				register_client(frm);
			}).addClass("btn-primary");
		} else {
			frm.add_custom_button(__("Login to Site"), function () {
				login_to_site(frm);
			}).addClass("btn-primary");
			frm.add_custom_button(
				__("Rotate Credentials"),
				function () {
					rotate_credentials(frm);
				},
				__("Actions")
			);
			frm.add_custom_button(
				__("Deregister Client"),
				function () {
					deregister_client(frm);
				},
				__("Actions")
			);
		}

		if (frappe.user.has_role("System Manager")) {
			frm.add_custom_button(__("View Credentials"), function () {
				frappe.call({
					method: "helpdesk.api.view_connection_credentials",
					args: { connection: frm.doc.name },
					freeze: true,
					freeze_message: __("Fetching credentials..."),
					callback(r) {
						if (r.message) {
							show_credentials_dialog(r.message, frm);
						}
					},
				});
			});
		}

		frm.add_custom_button(__("View Audit Log"), function () {
			load_and_show_audit_log(frm);
		});
	},
});

function register_client(frm) {
	if (!frm.doc.site_url) {
		frappe.msgprint(__("Site URL is required."));
		return;
	}
	if (!frm.doc.api_key) {
		frappe.msgprint(
			__(
				"API Key is required. On the customer site, open User <b>support@quarkcs.com</b>, generate API keys via <b>API Access</b>, and paste them into this form."
			)
		);
		return;
	}
	if (frm.is_dirty()) {
		frappe.msgprint(__("Save the form before registering."));
		return;
	}

	frappe.confirm(
		__(
			"This will call {0} as <b>support@quarkcs.com</b> (Token auth) and record this Hub as the registered one. Continue?",
			[frm.doc.site_url]
		),
		function () {
			frappe.call({
				method: "helpdesk.api.register_client",
				args: { connection: frm.doc.name },
				freeze: true,
				freeze_message: __("Registering client..."),
				callback(r) {
					if (r.message && r.message.status === "registered") {
						frappe.show_alert({
							message: __("Registered successfully"),
							indicator: "green",
						});
						frm.reload_doc();
					}
				},
			});
		}
	);
}

function login_to_site(frm) {
	frappe.call({
		method: "helpdesk.api.get_login_url",
		args: { connection: frm.doc.name },
		freeze: true,
		freeze_message: __("Generating login URL..."),
		callback(r) {
			if (r.message && r.message.login_url) {
				window.open(r.message.login_url, "_blank");
			} else {
				frappe.msgprint(__("Failed to generate login URL."));
			}
		},
	});
}

function deregister_client(frm) {
	frappe.confirm(
		__(
			"Deregister this client? The customer site's client_id will be cleared, but API keys will remain active until the customer admin revokes them. Continue?"
		),
		function () {
			frappe.call({
				method: "helpdesk.api.deregister_client",
				args: { connection: frm.doc.name },
				freeze: true,
				freeze_message: __("Deregistering..."),
				callback(r) {
					if (r.message && r.message.status === "deregistered") {
						frappe.show_alert({
							message: __("Deregistered"),
							indicator: "green",
						});
						frm.reload_doc();
					}
				},
			});
		}
	);
}

function rotate_credentials(frm) {
	frappe.confirm(
		__(
			"Generate new API credentials on the Hub and push them to {0}. Any other client (e.g. Claude Desktop) using the current credentials will stop working. Continue?",
			[frm.doc.site_url]
		),
		function () {
			frappe.call({
				method: "helpdesk.api.rotate_credentials",
				args: { connection: frm.doc.name },
				freeze: true,
				freeze_message: __("Rotating credentials..."),
				callback(r) {
					if (r.message && r.message.status === "rotated") {
						frappe.show_alert({
							message: __("Credentials rotated"),
							indicator: "green",
						});
						frm.reload_doc();
					}
				},
			});
		}
	);
}

function load_and_show_audit_log(frm) {
	frappe.call({
		method: "helpdesk.api.get_remote_audit_log",
		args: { connection: frm.doc.name, limit: 200 },
		freeze: true,
		freeze_message: __("Loading audit log..."),
		callback(r) {
			if (r.message) {
				show_audit_log_dialog(r.message.entries || [], frm);
			}
		},
	});
}

function show_audit_log_dialog(entries, frm) {
	var header_html =
		'<div style="margin-bottom:8px;color:#888;font-size:12px">' +
		"Showing " +
		entries.length +
		" entries. Audit log is written by the Hub after every MCP call." +
		"</div>";

	if (!entries || entries.length === 0) {
		var empty_html =
			header_html +
			'<div style="text-align:center;padding:24px;color:#888">No MCP activity logged yet for this connection.</div>';
		var d0 = new frappe.ui.Dialog({
			title: __("Audit Log - {0}", [frm.doc.customer_name || frm.doc.name]),
			size: "extra-large",
			fields: [{ fieldname: "html", fieldtype: "HTML", options: empty_html }],
		});
		d0.show();
		return;
	}

	var rows = "";
	for (var i = 0; i < entries.length; i++) {
		var e = entries[i];
		var status_color = e.status === "Success" ? "#4bc0c0" : "#ff6384";
		var type_color = e.action_type === "Write" ? "#ff9f40" : "#36a2eb";
		var args_short = (e.arguments || "").substring(0, 80);
		if ((e.arguments || "").length > 80) args_short += "...";

		rows +=
			'<tr style="border-bottom:1px solid #eee">' +
			'<td style="padding:6px;font-family:monospace;font-size:11px">' +
			(e.timestamp || "").substring(0, 19) +
			"</td>" +
			'<td style="padding:6px"><span style="background:' +
			type_color +
			';color:white;padding:1px 6px;border-radius:6px;font-size:10px">' +
			(e.action_type || "") +
			"</span></td>" +
			'<td style="padding:6px;font-weight:500">' +
			(e.tool_name || "") +
			"</td>" +
			'<td style="padding:6px;font-family:monospace;font-size:11px;color:#555">' +
			frappe.utils.escape_html(args_short) +
			"</td>" +
			'<td style="padding:6px"><span style="background:' +
			status_color +
			';color:white;padding:1px 6px;border-radius:6px;font-size:10px">' +
			(e.status || "") +
			"</span></td>" +
			'<td style="padding:6px;font-size:11px;color:#888">' +
			((e.execution_time_ms || 0) + "ms") +
			"</td>" +
			"</tr>";
	}

	var html =
		'<div style="max-height:60vh;overflow:auto">' +
		header_html +
		'<table style="width:100%;border-collapse:collapse;font-size:12px">' +
		'<thead><tr style="border-bottom:2px solid #ddd;text-align:left;background:#f4f5f6">' +
		'<th style="padding:6px">Timestamp</th>' +
		'<th style="padding:6px">Type</th>' +
		'<th style="padding:6px">Tool</th>' +
		'<th style="padding:6px">Arguments</th>' +
		'<th style="padding:6px">Status</th>' +
		'<th style="padding:6px">Time</th>' +
		"</tr></thead><tbody>" +
		rows +
		"</tbody></table></div>";

	var d = new frappe.ui.Dialog({
		title: __("Site Audit Log - {0}", [frm.doc.customer_name || frm.doc.name]),
		size: "extra-large",
		fields: [{ fieldname: "audit_html", fieldtype: "HTML", options: html }],
	});
	d.show();
}

function show_credentials_dialog(data, frm) {
	const d = new frappe.ui.Dialog({
		title: __("Credentials - {0}", [frm.doc.customer_name || frm.doc.name]),
		size: "large",
		fields: [
			{
				fieldname: "warning_html",
				fieldtype: "HTML",
				options: `<div style="padding:8px 12px;background:#fff3cd;border:1px solid #ffeaa7;border-radius:4px;margin-bottom:12px">
					<b>Security note:</b> This access is audit-logged. Anyone with these credentials can act as
					<b>support@quarkcs.com</b> on <b>${frappe.utils.escape_html(data.site_url)}</b>.
					If you use these in Claude Desktop or Claude Web App, avoid clicking <b>Rotate Credentials</b>
					while those tools are running - rotation invalidates the current keys everywhere.
				</div>`,
			},
			{
				fieldname: "api_key",
				fieldtype: "Data",
				label: __("API Key"),
				read_only: 1,
				default: data.api_key,
			},
			{
				fieldname: "api_secret",
				fieldtype: "Data",
				label: __("API Secret"),
				read_only: 1,
				default: data.api_secret,
			},
			{
				fieldname: "token",
				fieldtype: "Data",
				label: __("Token (key:secret)"),
				read_only: 1,
				default: data.token,
			},
			{
				fieldname: "mcp_url",
				fieldtype: "Data",
				label: __("MCP URL"),
				read_only: 1,
				default: data.mcp_url,
			},
			{ fieldname: "sb", fieldtype: "Section Break", label: __("Claude Desktop Config") },
			{
				fieldname: "desktop_config",
				fieldtype: "Code",
				label: __("Paste into claude_desktop_config.json"),
				options: "JSON",
				read_only: 1,
				default: data.desktop_config,
			},
		],
		primary_action_label: __("Copy Config"),
		primary_action() {
			navigator.clipboard.writeText(data.desktop_config).then(() => {
				frappe.show_alert({
					message: __("Config copied to clipboard"),
					indicator: "green",
				});
			});
		},
	});

	d.set_secondary_action_label(__("Copy Token"));
	d.set_secondary_action(() => {
		navigator.clipboard.writeText(data.token).then(() => {
			frappe.show_alert({ message: __("Token copied to clipboard"), indicator: "green" });
		});
	});

	d.show();
}
