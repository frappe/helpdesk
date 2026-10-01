# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Seed HDS Model Pricing from the FALLBACK_MODEL_COSTS constant.

Runs once on migrate. Only inserts models that do not already exist, so it is
safe to re-run and never overwrites a price an admin has edited in the UI.
"""

import frappe


def execute():
	from helpdesk.ai_engine import (
		FALLBACK_MODEL_COSTS,
		HAIKU_MODEL,
		OPUS_MODEL,
		SONNET_MODEL,
	)

	display_names = {
		HAIKU_MODEL: "Claude Haiku 4.5",
		SONNET_MODEL: "Claude Sonnet 4.6",
		OPUS_MODEL: "Claude Opus 4.7",
		"claude-sonnet-4-20250514": "Claude Sonnet 4 (deprecated)",
	}
	deprecated = {"claude-sonnet-4-20250514": "2026-06-15"}

	for model_id, costs in FALLBACK_MODEL_COSTS.items():
		if frappe.db.exists("HDS Model Pricing", model_id):
			continue

		doc = frappe.get_doc(
			{
				"doctype": "HDS Model Pricing",
				"model_id": model_id,
				"display_name": display_names.get(model_id, model_id),
				"provider": "Anthropic",
				"is_active": 0 if model_id in deprecated else 1,
				"deprecated_on": deprecated.get(model_id),
				"input_cost_per_1m": costs["input"],
				"output_cost_per_1m": costs["output"],
				"cache_read_cost_per_1m": costs["cache_read"],
				"cache_write_cost_per_1m": costs["cache_write"],
				"last_synced_on": frappe.utils.now_datetime(),
			}
		)
		doc.insert(ignore_permissions=True)

	frappe.db.commit()
