// Copyright (c) 2026, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

function setupForm({ doc, call, toast, $dialog }) {
	var actions = [];

	// Login to Site - first button
	actions.push({
		label: "Login to Site",
		onClick: async function () {
			try {
				var connections = await call("helpdesk.api.get_connections");
				if (!connections || connections.length === 0) {
					toast.error("No support connections configured.");
					return;
				}
				var activeConns = [];
				for (var i = 0; i < connections.length; i++) {
					if (connections[i].connection_status === "Connected") {
						activeConns.push(connections[i]);
					}
				}
				if (activeConns.length === 0) {
					toast.error("No active connections.");
					return;
				}

				// Prefer connections linked to this ticket's customer.
				var ticketCustomer = doc.customer || "";
				var forCustomer = [];
				if (ticketCustomer) {
					for (var j = 0; j < activeConns.length; j++) {
						if (activeConns[j].customer_name === ticketCustomer) {
							forCustomer.push(activeConns[j]);
						}
					}
				}
				var picklist = forCustomer.length > 0 ? forCustomer : activeConns;

				if (picklist.length === 1) {
					await doLogin(picklist[0].name, doc.name, call, toast);
				} else {
					showLoginPicker(picklist, call, toast, $dialog, doc);
				}
			} catch (error) {
				toast.error("Failed to login");
				console.error("Login error:", error);
			}
		},
	});

	// AI Triage - standalone button
	actions.push({
		label: "AI Triage",
		theme: "blue",
		variant: "subtle",
		onClick: async function () {
			try {
				var triage = await call("helpdesk.api.get_triage", { ticket: doc.name });
				if (triage.status === "Completed") {
					showTriageDialog(triage, doc, call, toast, $dialog);
				} else if (triage.status === "In Progress") {
					toast.info("Triage is in progress, please wait...");
				} else {
					showRetriageDialog(doc, call, toast, $dialog);
				}
			} catch (error) {
				toast.error("Failed to load triage");
				console.error("Triage error:", error);
			}
		},
	});

	// AI Tools dropdown - grouped actions
	actions.push({
		group: "AI Tools",
		buttonLabel: "AI Tools",
		hideLabel: true,
		items: [
			{
				label: "Start Investigation",
				onClick: async function () {
					try {
						var connections = await call("helpdesk.api.get_connections");
						showInvestigationDialog(connections, doc, call, toast, $dialog);
					} catch (error) {
						toast.error("Failed to load connections");
						console.error("Connections error:", error);
					}
				},
			},
			{
				label: "View Sessions",
				onClick: async function () {
					try {
						var sessions = await call("helpdesk.api.get_sessions", {
							ticket: doc.name,
						});
						showSessionsDialog(sessions, doc, call, toast, $dialog);
					} catch (error) {
						toast.error("Failed to load sessions");
						console.error("Sessions error:", error);
					}
				},
			},
			{
				label: "Re-run Triage",
				onClick: async function () {
					try {
						await call("helpdesk.api.run_triage_now", { ticket: doc.name });
						toast.success("Triage queued. Refresh in a few seconds.");
					} catch (error) {
						toast.error("Failed to queue triage");
						console.error("Retriage error:", error);
					}
				},
			},
		],
	});

	// Pending Actions button
	actions.push({
		label: "Approvals",
		onClick: async function () {
			try {
				var pending = await call("helpdesk.api.get_pending_actions", {
					ticket: doc.name,
				});
				if (!pending || pending.length === 0) {
					toast.info("No pending approvals for this ticket.");
					return;
				}
				// Load the first pending action request detail
				var detail = await call("helpdesk.api.get_action_request_detail", {
					action_request: pending[0].name,
				});
				showApprovalDialog(detail, doc, call, toast, $dialog);
			} catch (error) {
				toast.error("Failed to load approvals");
				console.error("Approvals error:", error);
			}
		},
	});

	return { actions: actions };
}

async function doLogin(connectionName, ticketName, call, toast) {
	try {
		var result = await call("helpdesk.api.get_login_url", {
			connection: connectionName,
			ticket: ticketName,
		});
		if (result && result.login_url) {
			window.open(result.login_url, "_blank");
		} else {
			toast.error("Failed to get login URL");
		}
	} catch (error) {
		var msg =
			(error && (error.message || error._server_messages || error.exception)) ||
			"Login failed";
		toast.error("Login failed: " + msg);
		console.error("Login error:", error);
	}
}

function showLoginPicker(connections, call, toast, $dialog, doc) {
	var optionsHtml = "";
	for (var i = 0; i < connections.length; i++) {
		var c = connections[i];
		optionsHtml +=
			'<option value="' + c.name + '">' + c.customer_name + " (" + c.site_url + ")</option>";
	}

	$dialog({
		title: "Login to Customer Site",
		html:
			'<div style="padding:8px"><label style="font-weight:bold;display:block;margin-bottom:4px">Select Connection</label>' +
			'<select id="qcs-login-conn" style="width:100%;padding:6px;border:1px solid #d1d5db;border-radius:4px">' +
			optionsHtml +
			"</select></div>",
		actions: [
			{
				label: "Login",
				variant: "solid",
				onClick: async function (_ref) {
					var connEl = document.getElementById("qcs-login-conn");
					if (connEl && connEl.value) {
						_ref.close();
						await doLogin(connEl.value, doc.name, call, toast);
					}
				},
			},
			{
				label: "Cancel",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function showTriageDialog(triage, doc, call, toast, $dialog) {
	var priorityColors = {
		Low: "#36a2eb",
		Medium: "#ffce56",
		High: "#ff9f40",
		Critical: "#ff6384",
	};

	var trackLabels = {
		ai_investigate: "AI Investigation",
		manual: "Manual Support",
		dev: "Developer Review",
		escalate: "Escalation Required",
	};

	var priorityColor = priorityColors[triage.priority] || "#999";
	var trackLabel = trackLabels[triage.recommended_track] || triage.recommended_track;

	// Build scope info
	var scopeHtml = "";
	var scope = triage.data && triage.data.scope;
	if (scope) {
		var parts = [];
		if (scope.period_start && scope.period_end) {
			parts.push("<b>Period:</b> " + scope.period_start + " to " + scope.period_end);
		}
		if (scope.specific_entities && scope.specific_entities.length) {
			parts.push("<b>Focus:</b> " + scope.specific_entities.join(", "));
		}
		if (scope.stated_constraint) {
			parts.push('<b>Customer said:</b> "' + scope.stated_constraint + '"');
		}
		if (parts.length) {
			scopeHtml =
				'<div style="margin-top:8px;padding:8px;background:#f4f5f6;border-radius:4px">' +
				parts.join("<br>") +
				"</div>";
		}
	}

	// Build investigation steps
	var stepsHtml = "";
	var steps = triage.data && triage.data.investigation_steps;
	if (steps && steps.length) {
		stepsHtml =
			'<div style="margin-top:8px"><b>Investigation Steps:</b><ol style="margin-top:4px">';
		for (var i = 0; i < steps.length; i++) {
			stepsHtml += "<li>" + steps[i] + "</li>";
		}
		stepsHtml += "</ol></div>";
	}

	var msg =
		'<div style="padding:8px">' +
		'<div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">' +
		'<span style="background:' +
		priorityColor +
		';color:white;padding:4px 12px;border-radius:12px;font-weight:bold">' +
		triage.priority +
		"</span>" +
		'<span style="background:#e8f4fd;padding:4px 12px;border-radius:12px">' +
		triage.category +
		"</span>" +
		'<span style="background:#f0f0f0;padding:4px 12px;border-radius:12px">' +
		triage.complexity +
		"</span>" +
		"</div>" +
		'<div style="margin-bottom:8px"><b>Summary:</b><br>' +
		triage.summary +
		"</div>" +
		'<div style="margin-bottom:8px"><b>Recommended:</b> ' +
		trackLabel +
		"</div>" +
		scopeHtml +
		stepsHtml +
		'<div style="margin-top:8px;color:#888;font-size:12px">Triaged at: ' +
		triage.timestamp +
		"</div>" +
		"</div>";

	$dialog({
		title: "AI Triage - Ticket #" + doc.name,
		html: msg,
		actions: [
			{
				label: "Start Investigation",
				variant: "solid",
				onClick: async function (_ref) {
					_ref.close();
					try {
						var connections = await call("helpdesk.api.get_connections");
						showInvestigationDialog(connections, doc, call, toast, $dialog);
					} catch (error) {
						toast.error("Failed to load connections");
					}
				},
			},
			{
				label: "Close",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function showRetriageDialog(doc, call, toast, $dialog) {
	$dialog({
		title: "AI Triage - Ticket #" + doc.name,
		message: "No triage results yet. Would you like to run AI triage on this ticket?",
		actions: [
			{
				label: "Run Triage",
				variant: "solid",
				onClick: async function (_ref) {
					try {
						await call("helpdesk.api.run_triage_now", { ticket: doc.name });
						toast.success("Triage queued. Refresh in a few seconds.");
						_ref.close();
					} catch (error) {
						toast.error("Failed to queue triage");
					}
				},
			},
			{
				label: "Cancel",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function showInvestigationDialog(connections, doc, call, toast, $dialog) {
	if (!connections || connections.length === 0) {
		toast.error("No support connections configured. Create a HDS Support Connection first.");
		return;
	}

	var activeConns = [];
	for (var i = 0; i < connections.length; i++) {
		if (connections[i].connection_status === "Connected") {
			activeConns.push(connections[i]);
		}
	}

	if (activeConns.length === 0) {
		toast.error("No active connections available.");
		return;
	}

	// Prefer connections linked to this ticket's customer.
	var ticketCustomer = doc.customer || "";
	var forCustomer = [];
	if (ticketCustomer) {
		for (var k = 0; k < activeConns.length; k++) {
			if (activeConns[k].customer_name === ticketCustomer) {
				forCustomer.push(activeConns[k]);
			}
		}
	}
	var picklist = forCustomer.length > 0 ? forCustomer : activeConns;

	var optionsHtml = "";
	for (var j = 0; j < picklist.length; j++) {
		var c = picklist[j];
		optionsHtml +=
			'<option value="' + c.name + '">' + c.customer_name + " (" + c.site_url + ")</option>";
	}

	var input_style =
		"width:100%;padding:6px;border:1px solid #d1d5db;border-radius:4px;font-size:13px";
	var label_style = "font-weight:500;display:block;margin-bottom:4px;font-size:13px";

	var msg =
		'<div style="padding:8px;max-height:70vh;overflow:auto">' +
		// Connection
		'<div style="margin-bottom:12px">' +
		'<label style="' +
		label_style +
		'">Connection *</label>' +
		'<select id="qcs-conn-select" style="' +
		input_style +
		'">' +
		optionsHtml +
		"</select></div>" +
		// Date range
		'<div style="display:flex;gap:8px;margin-bottom:12px">' +
		'<div style="flex:1"><label style="' +
		label_style +
		'">From Date</label>' +
		'<input type="date" id="qcs-date-from" style="' +
		input_style +
		'"/></div>' +
		'<div style="flex:1"><label style="' +
		label_style +
		'">To Date</label>' +
		'<input type="date" id="qcs-date-to" style="' +
		input_style +
		'"/></div>' +
		"</div>" +
		// Focus doctypes
		'<div style="margin-bottom:12px">' +
		'<label style="' +
		label_style +
		'">Focus DocTypes <span style="color:#888;font-weight:normal">(comma-separated)</span></label>' +
		'<input type="text" id="qcs-focus-doctypes" style="' +
		input_style +
		'" placeholder="Sales Invoice, Bank Transaction, Payment Entry"/>' +
		"</div>" +
		// Specific reports
		'<div style="margin-bottom:12px">' +
		'<label style="' +
		label_style +
		'">Reports to Check <span style="color:#888;font-weight:normal">(comma-separated)</span></label>' +
		'<input type="text" id="qcs-reports" style="' +
		input_style +
		'" placeholder="General Ledger, Bank Reconciliation Statement"/>' +
		"</div>" +
		// Free-form notes
		"<div>" +
		'<label style="' +
		label_style +
		'">Additional Notes</label>' +
		'<textarea id="qcs-agent-notes" rows="3" style="' +
		input_style +
		'" placeholder="Anything else the AI should know..."></textarea>' +
		"</div>" +
		"</div>";

	$dialog({
		title: "Start AI Investigation - Ticket #" + doc.name,
		html: msg,
		actions: [
			{
				label: "Start Investigation",
				variant: "solid",
				onClick: async function (_ref) {
					var connEl = document.getElementById("qcs-conn-select");
					var fromEl = document.getElementById("qcs-date-from");
					var toEl = document.getElementById("qcs-date-to");
					var focusEl = document.getElementById("qcs-focus-doctypes");
					var reportsEl = document.getElementById("qcs-reports");
					var notesEl = document.getElementById("qcs-agent-notes");

					var connName = connEl ? connEl.value : "";
					if (!connName) {
						toast.error("Select a connection");
						return;
					}

					// Build structured notes
					var parts = [];
					if (fromEl && fromEl.value && toEl && toEl.value) {
						parts.push("Investigation scope: " + fromEl.value + " to " + toEl.value);
					} else if (fromEl && fromEl.value) {
						parts.push("From date: " + fromEl.value);
					} else if (toEl && toEl.value) {
						parts.push("Up to date: " + toEl.value);
					}
					if (focusEl && focusEl.value.trim()) {
						parts.push("Focus DocTypes: " + focusEl.value.trim());
					}
					if (reportsEl && reportsEl.value.trim()) {
						parts.push("Reports to check: " + reportsEl.value.trim());
					}
					if (notesEl && notesEl.value.trim()) {
						parts.push("Notes: " + notesEl.value.trim());
					}
					var agentNotes = parts.join("\n");

					try {
						var result = await call("helpdesk.api.start_investigation", {
							ticket: doc.name,
							connection: connName,
							agent_notes: agentNotes,
						});
						toast.success("Investigation started: " + result.session);
						_ref.close();
					} catch (error) {
						toast.error("Failed to start investigation");
						console.error("Investigation error:", error);
					}
				},
			},
			{
				label: "Cancel",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function showSessionsDialog(sessions, doc, call, toast, $dialog) {
	if (!sessions || sessions.length === 0) {
		$dialog({
			title: "AI Sessions - Ticket #" + doc.name,
			message: "No investigation sessions yet.",
			actions: [
				{
					label: "Close",
					onClick: function (_ref) {
						_ref.close();
					},
				},
			],
		});
		return;
	}

	var statusColors = {
		Active: "#36a2eb",
		"Awaiting Review": "#ff9f40",
		Completed: "#4bc0c0",
		Failed: "#ff6384",
		Cancelled: "#999",
	};

	var cardsHtml = "";
	for (var i = 0; i < sessions.length; i++) {
		var s = sessions[i];
		var color = statusColors[s.status] || "#999";
		var tools = s.total_tool_calls || 0;

		// Render diagnosis preview (first 200 chars)
		var diagPreview = "";
		if (s.diagnosis) {
			var plain = s.diagnosis.replace(/[#*_`]/g, "").substring(0, 150);
			diagPreview =
				'<div style="margin-top:8px;color:#555;font-size:13px">' + plain + "...</div>";
		}

		// Action buttons vary by status
		var action_buttons =
			"<button onclick=\"window._qcsShowDiagnosis('" +
			s.name +
			'\')" style="padding:4px 12px;border:1px solid #d1d5db;border-radius:4px;background:white;cursor:pointer;font-size:12px">View Diagnosis</button>' +
			"<button onclick=\"window._qcsCopyDiagnosis('" +
			s.name +
			'\')" style="padding:4px 12px;border:1px solid #d1d5db;border-radius:4px;background:white;cursor:pointer;font-size:12px">Copy</button>';

		if (s.status === "Awaiting Review") {
			action_buttons +=
				"<button onclick=\"window._qcsResumeSession('" +
				s.name +
				'\')" style="padding:4px 12px;border:none;border-radius:4px;background:#ff9f40;color:white;cursor:pointer;font-size:12px">Continue Investigation</button>' +
				"<button onclick=\"window._qcsCancelSession('" +
				s.name +
				'\')" style="padding:4px 12px;border:1px solid #d1d5db;border-radius:4px;background:white;cursor:pointer;font-size:12px">Cancel</button>';
		}

		cardsHtml +=
			'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px">' +
			'<div style="display:flex;justify-content:space-between;align-items:center">' +
			'<div style="display:flex;gap:8px;align-items:center">' +
			'<span style="font-weight:bold">' +
			s.name +
			"</span>" +
			'<span style="background:' +
			color +
			';color:white;padding:2px 8px;border-radius:8px;font-size:11px">' +
			s.status +
			"</span>" +
			"</div>" +
			'<div style="display:flex;gap:12px;color:#888;font-size:12px">' +
			"<span>" +
			tools +
			" calls</span>" +
			"</div></div>" +
			diagPreview +
			'<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">' +
			action_buttons +
			"</div></div>";
	}

	// Store diagnoses globally for the onclick handlers
	window._qcsDiagnoses = {};
	for (var j = 0; j < sessions.length; j++) {
		window._qcsDiagnoses[sessions[j].name] =
			sessions[j].diagnosis || "No diagnosis available.";
	}
	window._qcsShowDiagnosis = async function (name) {
		// Fetch full session details (including MCP calls)
		var detail;
		try {
			detail = await call("helpdesk.api.get_session_detail", { session: name });
		} catch (e) {
			detail = { name: name, diagnosis: window._qcsDiagnoses[name] || "" };
		}
		showDiagnosisDetailDialog(detail, $dialog);
	};
	window._qcsCopyDiagnosis = function (name) {
		var diag = window._qcsDiagnoses[name] || "";
		navigator.clipboard.writeText(diag);
	};

	window._qcsResumeSession = function (name) {
		showResumeDialog(name, doc, call, toast, $dialog);
	};

	window._qcsCancelSession = async function (name) {
		if (!confirm("Cancel this session? This cannot be undone.")) return;
		try {
			await call("helpdesk.api.cancel_session", { session: name });
			toast.success("Session cancelled");
			// Note: dialog won't auto-refresh; user can reopen "View Sessions"
		} catch (error) {
			toast.error("Failed to cancel");
			console.error(error);
		}
	};

	var html = '<div style="padding:8px">' + cardsHtml + "</div>";

	$dialog({
		title: "AI Sessions - Ticket #" + doc.name,
		html: html,
		actions: [
			{
				label: "Close",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function showResumeDialog(sessionName, doc, call, toast, $dialog) {
	var html =
		'<div style="padding:8px">' +
		'<div style="padding:8px;background:#fff3cd;border:1px solid #ffeaa7;border-radius:4px;margin-bottom:12px;font-size:13px">' +
		"<b>Session " +
		sessionName +
		"</b> has completed its initial investigation steps and is awaiting your direction for deeper investigation." +
		"</div>" +
		'<label style="font-weight:500;display:block;margin-bottom:4px;font-size:13px">Guidance for Deep Dive <span style="color:#888;font-weight:normal">(optional)</span></label>' +
		'<textarea id="qcs-resume-guidance" rows="5" style="width:100%;padding:6px;border:1px solid #d1d5db;border-radius:4px;font-size:13px" ' +
		'placeholder="Tell the AI what to focus on next. E.g. &quot;Check Payment Entry references for the mismatched invoices&quot; or &quot;Investigate why bank_account is null on the specific PEs you found&quot;."></textarea>' +
		"</div>";

	$dialog({
		title: "Continue Investigation - " + sessionName,
		html: html,
		actions: [
			{
				label: "Continue",
				variant: "solid",
				onClick: async function (_ref) {
					var el = document.getElementById("qcs-resume-guidance");
					var guidance = el ? el.value : "";
					try {
						await call("helpdesk.api.resume_session", {
							session: sessionName,
							agent_guidance: guidance,
						});
						toast.success("Investigation resuming...");
						_ref.close();
					} catch (error) {
						toast.error("Failed to resume");
						console.error(error);
					}
				},
			},
			{
				label: "Cancel",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function showDiagnosisDetailDialog(detail, $dialog) {
	var diag = detail.diagnosis || "No diagnosis available.";
	var rendered = mdToHtml(diag);

	// Session metadata
	var duration = "-";
	if (detail.started_at && detail.ended_at) {
		var sec = Math.round((new Date(detail.ended_at) - new Date(detail.started_at)) / 1000);
		duration = sec < 60 ? sec + "s" : Math.floor(sec / 60) + "m " + (sec % 60) + "s";
	}
	var cost = detail.estimated_cost_usd
		? "$" + Number(detail.estimated_cost_usd).toFixed(4)
		: "-";
	var totalTokens = (detail.total_input_tokens || 0) + (detail.total_output_tokens || 0);

	var statusColors = {
		Active: "#36a2eb",
		Completed: "#4bc0c0",
		Failed: "#ff6384",
		Cancelled: "#999",
	};
	var statusColor = statusColors[detail.status] || "#999";

	var meta_html =
		'<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:10px;margin-bottom:12px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:12px">' +
		'<div><b>Status:</b> <span style="background:' +
		statusColor +
		';color:white;padding:1px 6px;border-radius:6px;font-size:10px">' +
		(detail.status || "") +
		"</span></div>" +
		"<div><b>Model:</b> " +
		(detail.model_used || "-") +
		"</div>" +
		"<div><b>Duration:</b> " +
		duration +
		"</div>" +
		"<div><b>Tool Calls:</b> " +
		(detail.total_tool_calls || 0) +
		"</div>" +
		"<div><b>Tokens:</b> " +
		totalTokens.toLocaleString() +
		"</div>" +
		"<div><b>Cost:</b> " +
		cost +
		"</div>" +
		"</div>";

	// MCP call timeline
	var timeline_html = "";
	var mcp_calls = detail.mcp_calls || [];
	if (mcp_calls.length) {
		var rows = "";
		for (var i = 0; i < mcp_calls.length; i++) {
			var c = mcp_calls[i];
			var type_color = c.action_type === "Write" ? "#ff9f40" : "#36a2eb";
			rows +=
				'<tr style="border-bottom:1px solid #eee">' +
				'<td style="padding:4px 8px;color:#888;font-family:monospace;font-size:11px">' +
				(i + 1) +
				"</td>" +
				'<td style="padding:4px 8px"><span style="background:' +
				type_color +
				';color:white;padding:1px 6px;border-radius:6px;font-size:10px">' +
				(c.action_type || "Read") +
				"</span></td>" +
				'<td style="padding:4px 8px;font-weight:500">' +
				(c.tool_name || "") +
				"</td>" +
				'<td style="padding:4px 8px;font-family:monospace;font-size:11px;color:#555;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' +
				frappe.utils.escape_html((c.arguments || "").substring(0, 120)) +
				"</td>" +
				'<td style="padding:4px 8px;color:#888;font-size:11px">' +
				(c.execution_time_ms || 0) +
				"ms</td>" +
				"</tr>";
		}
		timeline_html =
			'<details style="margin-bottom:12px"><summary style="cursor:pointer;font-weight:500;color:#555;padding:6px 0">MCP Call Timeline (' +
			mcp_calls.length +
			" calls)</summary>" +
			'<div style="max-height:240px;overflow:auto;border:1px solid #e5e7eb;border-radius:4px;margin-top:6px">' +
			'<table style="width:100%;border-collapse:collapse;font-size:12px"><thead>' +
			'<tr style="background:#f4f5f6;border-bottom:2px solid #ddd"><th style="padding:4px 8px;text-align:left">#</th><th style="padding:4px 8px;text-align:left">Type</th><th style="padding:4px 8px;text-align:left">Tool</th><th style="padding:4px 8px;text-align:left">Arguments</th><th style="padding:4px 8px;text-align:left">Time</th></tr>' +
			"</thead><tbody>" +
			rows +
			"</tbody></table></div></details>";
	}

	// Agent notes
	var notes_html = "";
	if (detail.agent_notes) {
		notes_html =
			'<div style="background:#fff3cd;border:1px solid #ffeaa7;border-radius:4px;padding:8px;margin-bottom:12px;font-size:13px">' +
			"<b>Agent Notes:</b> " +
			frappe.utils.escape_html(detail.agent_notes) +
			"</div>";
	}

	// Full html
	var full_html =
		'<div style="padding:8px;max-height:70vh;overflow:auto">' +
		meta_html +
		notes_html +
		timeline_html +
		'<div style="border-top:1px solid #eee;padding-top:8px;font-size:14px;line-height:1.6">' +
		rendered +
		"</div></div>";

	// Helpdesk's $dialog - only dialog API available in HD Form Script context
	$dialog({
		title: "Diagnosis - " + detail.name,
		html: full_html,
		actions: [
			{
				label: "Copy Diagnosis",
				variant: "solid",
				onClick: function (_ref) {
					navigator.clipboard.writeText(diag);
				},
			},
			{
				label: "Open in Desk",
				onClick: function (_ref) {
					window.open("/app/qcs-ai-support-session/" + detail.name, "_blank");
				},
			},
			{
				label: "Close",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}

function mdToHtml(md) {
	if (!md) return "";
	// Simple markdown to HTML converter
	var html = md
		// Escape HTML
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		// Headers
		.replace(/^### (.+)$/gm, '<h4 style="margin:12px 0 4px;font-size:14px">$1</h4>')
		.replace(
			/^## (.+)$/gm,
			'<h3 style="margin:16px 0 6px;font-size:16px;border-bottom:1px solid #eee;padding-bottom:4px">$1</h3>'
		)
		.replace(/^# (.+)$/gm, '<h2 style="margin:16px 0 8px;font-size:18px">$1</h2>')
		// Bold
		.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
		// Italic
		.replace(/\*(.+?)\*/g, "<i>$1</i>")
		// Code blocks
		.replace(/```[\s\S]*?```/g, function (match) {
			var code = match.replace(/```\w*\n?/, "").replace(/```$/, "");
			return (
				'<pre style="background:#f4f5f6;padding:8px;border-radius:4px;font-size:12px;overflow:auto;margin:8px 0">' +
				code +
				"</pre>"
			);
		})
		// Inline code
		.replace(
			/`(.+?)`/g,
			'<code style="background:#f4f5f6;padding:1px 4px;border-radius:2px;font-size:12px">$1</code>'
		)
		// Numbered lists
		.replace(/^\d+\.\s(.+)$/gm, '<li style="margin:2px 0">$1</li>')
		// Bullet lists
		.replace(/^[-*]\s(.+)$/gm, '<li style="margin:2px 0">$1</li>')
		// Horizontal rules
		.replace(/^---$/gm, '<hr style="border:none;border-top:1px solid #e5e7eb;margin:12px 0">')
		// Line breaks (double newline = paragraph)
		.replace(/\n\n/g, '</p><p style="margin:8px 0">')
		// Single newlines
		.replace(/\n/g, "<br>");

	return '<div style="font-size:14px"><p style="margin:8px 0">' + html + "</p></div>";
}

function showApprovalDialog(ar, doc, call, toast, $dialog) {
	var riskColors = {
		Low: "#4bc0c0",
		Medium: "#ffce56",
		High: "#ff6384",
	};

	var actionsHtml = "";
	var actions = ar.proposed_actions || [];
	for (var i = 0; i < actions.length; i++) {
		var a = actions[i];
		var riskColor = riskColors[a.risk_level] || "#999";
		var args = "";
		try {
			var parsed = JSON.parse(a.arguments || "{}");
			args = JSON.stringify(parsed, null, 2);
		} catch (e) {
			args = a.arguments || "";
		}

		actionsHtml +=
			'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px">' +
			'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">' +
			'<div style="display:flex;gap:8px;align-items:center">' +
			'<input type="checkbox" id="qcs-approve-' +
			i +
			'" checked style="width:16px;height:16px">' +
			"<b>" +
			a.tool_name +
			"</b>" +
			"</div>" +
			'<span style="background:' +
			riskColor +
			';color:white;padding:2px 8px;border-radius:8px;font-size:11px">' +
			a.risk_level +
			" risk</span>" +
			"</div>" +
			(a.description
				? '<div style="margin-bottom:6px;color:#555">' + a.description + "</div>"
				: "") +
			'<pre style="background:#f4f5f6;padding:8px;border-radius:4px;font-size:12px;overflow:auto;max-height:120px;margin:0">' +
			args +
			"</pre>" +
			"</div>";
	}

	var diagnosisHtml = "";
	if (ar.diagnosis) {
		var diagShort =
			ar.diagnosis.length > 300 ? ar.diagnosis.substring(0, 300) + "..." : ar.diagnosis;
		diagnosisHtml =
			'<div style="margin-bottom:12px;padding:8px;background:#f0f7ff;border-radius:4px">' +
			"<b>AI Diagnosis:</b><br>" +
			mdToHtml(diagShort) +
			"</div>";
	}

	var html =
		'<div style="padding:8px">' +
		'<div style="margin-bottom:8px;color:#888">Request: ' +
		ar.name +
		" | Session: " +
		(ar.session || "N/A") +
		"</div>" +
		diagnosisHtml +
		'<div style="margin-bottom:8px"><b>Proposed Actions (' +
		actions.length +
		"):</b></div>" +
		actionsHtml +
		"</div>";

	$dialog({
		title: "Approve Actions - Ticket #" + doc.name,
		html: html,
		actions: [
			{
				label: "Approve & Execute",
				variant: "solid",
				onClick: async function (_ref) {
					// Collect approved indices
					var approved = [];
					for (var j = 0; j < actions.length; j++) {
						var cb = document.getElementById("qcs-approve-" + j);
						if (cb && cb.checked) {
							approved.push(j);
						}
					}
					if (approved.length === 0) {
						toast.error("No actions selected");
						return;
					}
					try {
						var result = await call("helpdesk.api.approve_and_execute", {
							action_request: ar.name,
							approved_indices: JSON.stringify(approved),
							execute: 1,
						});
						var execResult = result.execution || {};
						toast.success("Executed: " + (execResult.status || "done"));
						_ref.close();
					} catch (error) {
						toast.error("Execution failed");
						console.error("Approval error:", error);
					}
				},
			},
			{
				label: "Reject All",
				onClick: async function (_ref) {
					try {
						await call("helpdesk.api.reject_action_request", {
							action_request: ar.name,
						});
						toast.success("Actions rejected");
						_ref.close();
					} catch (error) {
						toast.error("Failed to reject");
					}
				},
			},
			{
				label: "Cancel",
				onClick: function (_ref) {
					_ref.close();
				},
			},
		],
	});
}
