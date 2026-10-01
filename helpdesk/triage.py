# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Haiku auto-triage engine with loop guards.

Trigger: HD Ticket after_insert → enqueue background job
Model: Claude Haiku 4.5 (~$0.003 per ticket)
"""

import json

import anthropic
import frappe
from frappe.utils import now_datetime

from helpdesk.ai_engine import call_haiku

# Guard constants
MAX_TRIAGE_RETRIES = 2
TRIAGE_COOLDOWN_SECONDS = 30
TRIAGE_LOCK_TIMEOUT = 60
MAX_CONCURRENT_TRIAGES = 10
TRIAGE_JOB_TIMEOUT = 25

TRIAGE_SYSTEM_PROMPT = """You are an ERPNext/Frappe support triage AI. Analyze the support ticket and return a JSON object with your assessment.

You must return ONLY valid JSON with these exact fields:
{
  "category": "one of: Account, Billing, Configuration, Data, Integration, Performance, Permissions, Print, Report, Stock, Workflow, Other",
  "priority": "one of: Low, Medium, High, Critical",
  "complexity": "one of: Functional, Configuration, Data, Dev, Infrastructure",
  "summary": "2-3 sentence summary of the issue and likely cause",
  "recommended_track": "one of: ai_investigate, manual, dev, escalate",
  "scope": {
    "period_start": "YYYY-MM-DD or null if not mentioned",
    "period_end": "YYYY-MM-DD or null if not mentioned",
    "specific_entities": ["list of specific doctypes, accounts, or items mentioned"],
    "stated_constraint": "any specific scope the customer mentioned, verbatim"
  },
  "key_doctypes": ["list of ERPNext doctypes likely involved"],
  "investigation_steps": ["3-5 recommended investigation steps"]
}

Rules:
- recommended_track = "ai_investigate" for issues that can be diagnosed by querying data (reports wrong, reconciliation issues, data mismatches)
- recommended_track = "manual" for simple how-to questions or UI guidance
- recommended_track = "dev" for bugs, custom code issues, or feature requests
- recommended_track = "escalate" for critical production-down issues
- Extract ALL date references and convert relative dates to absolute (e.g., "last 2 months" → actual date range)
- Extract ALL specific reports, documents, or entities the customer mentions
"""


def auto_triage_ticket(doc, method):
	"""after_insert hook for HD Ticket. Enqueues triage with guards."""
	# Guard: check if auto-triage is enabled in Hub Settings
	try:
		from helpdesk.ai_engine import get_hub_settings

		if not get_hub_settings().auto_triage_enabled:
			return
	except Exception:
		return

	# Guard: only triage new tickets
	if doc.docstatus != 0:
		return

	# Guard: skip if already triaged
	if doc.get("custom_triage_status") and doc.custom_triage_status not in ("", "Pending"):
		return

	# Guard: check concurrent limit
	active_jobs = frappe.cache.get_value("triage_active_count") or 0
	if active_jobs >= MAX_CONCURRENT_TRIAGES:
		frappe.logger().warning(
			f"Triage queue full ({active_jobs}/{MAX_CONCURRENT_TRIAGES}), skipping ticket {doc.name}"
		)
		return

	# Mark as pending
	frappe.db.set_value("HD Ticket", doc.name, "custom_triage_status", "Pending", update_modified=False)

	# Enqueue with deduplication
	frappe.enqueue(
		"helpdesk.triage.run_triage",
		ticket_id=doc.name,
		job_id=f"triage-{doc.name}",
		deduplicate=True,
		timeout=TRIAGE_JOB_TIMEOUT,
		queue="short",
	)


def run_triage_now(ticket_id: str):
	"""Manual trigger with cooldown + retry limit check."""
	ticket = frappe.get_doc("HD Ticket", ticket_id)

	# Guard: cooldown
	if ticket.custom_triage_timestamp:
		elapsed = (now_datetime() - ticket.custom_triage_timestamp).total_seconds()
		if elapsed < TRIAGE_COOLDOWN_SECONDS:
			frappe.throw(f"Triage cooldown: wait {int(TRIAGE_COOLDOWN_SECONDS - elapsed)}s")

	# Guard: retry limit
	triage_data = json.loads(ticket.custom_triage_data or "{}") if ticket.custom_triage_data else {}
	retry_count = triage_data.get("retry_count", 0)
	if retry_count >= MAX_TRIAGE_RETRIES:
		frappe.throw(f"Triage retry limit reached ({MAX_TRIAGE_RETRIES})")

	frappe.enqueue(
		"helpdesk.triage.run_triage",
		ticket_id=ticket_id,
		is_retry=retry_count > 0,
		job_id=f"triage-{ticket_id}",
		deduplicate=True,
		timeout=TRIAGE_JOB_TIMEOUT,
		queue="short",
	)

	return {"status": "enqueued", "ticket": ticket_id}


def run_triage(ticket_id: str, is_retry: bool = False):
	"""Background job: run Haiku triage with Redis lock."""
	lock_key = f"triage_lock:{ticket_id}"

	# Guard: Redis lock (prevent concurrent triage on same ticket)
	# Use raw Redis SET with NX (set if not exists) + EX (expiry)
	lock_acquired = frappe.cache.set(lock_key, 1, nx=True, ex=TRIAGE_LOCK_TIMEOUT)
	if not lock_acquired:
		frappe.logger().warning(f"Triage already running for ticket {ticket_id}")
		return

	# Track concurrent count
	frappe.cache.set_value("triage_active_count", (frappe.cache.get_value("triage_active_count") or 0) + 1)

	try:
		# Guard: check ticket still exists and is open
		if not frappe.db.exists("HD Ticket", ticket_id):
			return

		status = frappe.db.get_value("HD Ticket", ticket_id, "status")
		if status == "Closed":
			frappe.db.set_value(
				"HD Ticket", ticket_id, "custom_triage_status", "Skipped", update_modified=False
			)
			return

		# Mark in progress
		frappe.db.set_value(
			"HD Ticket", ticket_id, "custom_triage_status", "In Progress", update_modified=False
		)
		frappe.db.commit()

		# Build triage input
		ticket = frappe.get_doc("HD Ticket", ticket_id)
		user_message = _build_triage_input(ticket)

		# Guard: insufficient text content (image-only, empty tickets)
		if user_message is None:
			frappe.db.set_value(
				"HD Ticket",
				ticket_id,
				{
					"custom_triage_status": "Skipped",
					"custom_triage_summary": "Insufficient text content for auto-triage (possibly image-only ticket)",
					"custom_triage_recommended_track": "manual",
					"custom_triage_timestamp": now_datetime(),
				},
				update_modified=False,
			)
			frappe.db.commit()
			return

		# Call the triage model. Anchor today's date so relative ranges like
		# "last 2 months" resolve to the right year — without this, models
		# guess and get it wrong (found while evaluating providers).
		from frappe.utils import nowdate

		user_message = f"Today's date: {nowdate()}\n\n{user_message}"
		result = call_haiku(TRIAGE_SYSTEM_PROMPT, user_message, ticket_name=ticket_id)
		triage = result["response"]

		# Get existing triage data for retry tracking
		existing_data = json.loads(ticket.custom_triage_data or "{}") if ticket.custom_triage_data else {}
		retry_count = existing_data.get("retry_count", 0) + (1 if is_retry else 0)

		# Store results using db_set to avoid triggering hooks
		triage_data = {
			**triage,
			"retry_count": retry_count,
			"usage": result["usage"],
			"cost_usd": result["cost"],
		}

		updates = {
			"custom_triage_status": "Completed",
			"custom_triage_category": triage.get("category", ""),
			"custom_triage_priority": triage.get("priority", ""),
			"custom_triage_complexity": triage.get("complexity", ""),
			"custom_triage_summary": triage.get("summary", ""),
			"custom_triage_recommended_track": triage.get("recommended_track", ""),
			"custom_triage_data": json.dumps(triage_data),
			"custom_triage_timestamp": now_datetime(),
		}

		for field, value in updates.items():
			frappe.db.set_value("HD Ticket", ticket_id, field, value, update_modified=False)

		frappe.db.commit()

		# Post triage comment (with skip_notifications to prevent cascades)
		_post_triage_comment(ticket_id, triage)

	except anthropic.APIError as e:
		# API rate limit or error - mark failed, no retry
		frappe.db.set_value("HD Ticket", ticket_id, "custom_triage_status", "Failed", update_modified=False)
		frappe.db.commit()
		frappe.log_error(f"Triage API error for ticket {ticket_id}", str(e))

	except Exception as e:
		frappe.db.set_value("HD Ticket", ticket_id, "custom_triage_status", "Failed", update_modified=False)
		frappe.db.commit()
		frappe.log_error(f"Triage error for ticket {ticket_id}", str(e))

	finally:
		# Release lock and decrement counter
		frappe.cache.delete_value(lock_key)
		active = frappe.cache.get_value("triage_active_count") or 1
		frappe.cache.set_value("triage_active_count", max(0, active - 1))


def _build_triage_input(ticket):
	"""Build the user message from ticket data.

	Returns None if there's insufficient text content for triage
	(e.g. image-only tickets with no subject or description text).
	"""
	subject = (ticket.subject or "").strip()
	desc = ""
	if ticket.description:
		desc = frappe.utils.strip_html_tags(ticket.description).strip()

	# Check if there's enough text to triage
	total_text = subject + " " + desc
	if len(total_text.strip()) < 10:
		return None

	parts = []
	if subject:
		parts.append("Subject: %s" % subject)
	if desc:
		parts.append("Description: %s" % desc)
	if ticket.raised_by:
		parts.append("Raised by: %s" % ticket.raised_by)
	if ticket.ticket_type:
		parts.append("Type: %s" % ticket.ticket_type)
	if ticket.priority:
		parts.append("Customer Priority: %s" % ticket.priority)

	return "\n".join(parts)


def _post_triage_comment(ticket_id: str, triage: dict):
	"""Post a summary comment on the ticket."""
	priority = triage.get("priority", "Unknown")
	category = triage.get("category", "Unknown")
	summary = triage.get("summary", "")
	track = triage.get("recommended_track", "")

	track_labels = {
		"ai_investigate": "AI Investigation",
		"manual": "Manual Support",
		"dev": "Developer Review",
		"escalate": "Escalation",
	}

	comment_text = (
		f"<b>AI Triage:</b> {priority} priority | {category}<br>"
		f"<b>Summary:</b> {summary}<br>"
		f"<b>Recommended:</b> {track_labels.get(track, track)}"
	)

	comment = frappe.get_doc(
		{
			"doctype": "HD Ticket Comment",
			"reference_ticket": ticket_id,
			"content": comment_text,
			"commented_by": "Administrator",
		}
	)
	comment.flags.skip_notifications = True
	comment.insert(ignore_permissions=True)
	frappe.db.commit()
