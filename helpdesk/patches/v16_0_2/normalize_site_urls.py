# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Backfill: normalize HDS Support Connection.site_url + mcp_endpoint.

Converts bare hostnames (e.g. "qcssupport.localhost") to fully qualified URLs
(e.g. "http://qcssupport.localhost") so downstream consumers can use them
directly without scheme inference.
"""

import frappe

from helpdesk.utils import normalize_site_url


def execute():
	connections = frappe.get_all(
		"HDS Support Connection",
		fields=["name", "site_url", "mcp_endpoint"],
	)
	for conn in connections:
		if not conn.site_url:
			continue
		normalized = normalize_site_url(conn.site_url)
		mcp_endpoint = f"{normalized}/api/method/qcs_support_client.mcp.handler.handle"
		if normalized == conn.site_url and mcp_endpoint == conn.mcp_endpoint:
			continue
		frappe.db.set_value(
			"HDS Support Connection",
			conn.name,
			{"site_url": normalized, "mcp_endpoint": mcp_endpoint},
			update_modified=False,
		)
	frappe.db.commit()
