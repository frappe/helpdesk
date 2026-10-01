# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Anthropic API wrapper with prompt caching and token tracking."""

import json

import anthropic
import frappe

# Default model constants (can be overridden in HDS Hub Settings)
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"
OPUS_MODEL = "claude-opus-4-7"

# Fallback prices (USD per 1M tokens) used if HDS Model Pricing record is missing.
# The authoritative source is the HDS Model Pricing DocType - update prices there, not here.
FALLBACK_MODEL_COSTS = {
	HAIKU_MODEL: {"input": 1.00, "output": 5.00, "cache_read": 0.10, "cache_write": 1.25},
	SONNET_MODEL: {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
	OPUS_MODEL: {"input": 5.00, "output": 25.00, "cache_read": 0.50, "cache_write": 6.25},
	# Legacy / deprecated (retires 2026-06-15) - kept so old logs still price correctly
	"claude-sonnet-4-20250514": {
		"input": 3.00,
		"output": 15.00,
		"cache_read": 0.30,
		"cache_write": 3.75,
	},
}


def get_model_cost(model: str) -> dict:
	"""Return per-1M-token costs for a model.

	Order of precedence:
	1. HDS Model Pricing DocType record for this model_id (the UI-editable source of truth)
	2. FALLBACK_MODEL_COSTS constant (ships with the code so pricing works before seeding)
	3. Zeros (unknown model - cost will be 0)
	"""
	try:
		row = frappe.db.get_value(
			"HDS Model Pricing",
			model,
			[
				"input_cost_per_1m",
				"output_cost_per_1m",
				"cache_read_cost_per_1m",
				"cache_write_cost_per_1m",
			],
			as_dict=True,
		)
		if row:
			return {
				"input": row.input_cost_per_1m or 0,
				"output": row.output_cost_per_1m or 0,
				"cache_read": row.cache_read_cost_per_1m or 0,
				"cache_write": row.cache_write_cost_per_1m or 0,
			}
	except Exception:
		pass

	return FALLBACK_MODEL_COSTS.get(model, {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0})


def get_hub_settings():
	"""Get HDS Hub Settings singleton."""
	return frappe.get_single("HDS Hub Settings")


def get_models():
	"""Get configured model IDs from Hub Settings."""
	try:
		settings = get_hub_settings()
		haiku = settings.default_triage_model or HAIKU_MODEL
		sonnet = settings.default_investigation_model or SONNET_MODEL
	except Exception:
		haiku = HAIKU_MODEL
		sonnet = SONNET_MODEL
	return haiku, sonnet


def get_provider_config(layer="triage"):
	"""Return (provider, base_url, api_key) from HDS Hub Settings.

	provider is one of: "Anthropic", "Anthropic Compatible", "OpenAI Compatible".
	The key lives ONLY on the Hub — customer sites never hold an AI credential.
	"""
	from frappe.utils.password import get_decrypted_password

	settings = get_hub_settings()
	provider = getattr(settings, "ai_provider", None) or "Anthropic"
	base_url = (getattr(settings, "ai_base_url", None) or "").rstrip("/") or None
	key_field = "anthropic_api_key"

	# Split providers: investigation may run on a different (tool-use capable)
	# provider than the cheap always-on triage layer.
	if layer == "investigation" and getattr(settings, "investigation_provider", None):
		provider = settings.investigation_provider
		base_url = (getattr(settings, "investigation_base_url", None) or "").rstrip("/") or None
		if get_decrypted_password(
			"HDS Hub Settings", "HDS Hub Settings", "investigation_api_key", raise_exception=False
		):
			key_field = "investigation_api_key"

	api_key = get_decrypted_password(
		"HDS Hub Settings", "HDS Hub Settings", key_field, raise_exception=False
	)
	# Fallback to site_config for backward compatibility
	if not api_key:
		api_key = frappe.conf.get("anthropic_api_key")

	if not api_key:
		frappe.throw("AI API key not configured. Go to HDS Hub Settings to set it.")
	if provider != "Anthropic" and not base_url:
		frappe.throw("Base URL is required for %s providers. Go to HDS Hub Settings." % provider)

	return provider, base_url, api_key


def get_client():
	"""Get an Anthropic-SDK client (native or a compatible endpoint).

	Anthropic-compatible providers (Kimi/Moonshot, GLM/Zhipu) accept the same
	API shape, so the only difference is base_url. OpenAI-compatible providers
	cannot be driven through this SDK — callers that need tool-use sessions
	get a clear error instead of a confusing HTTP failure.
	"""
	provider, base_url, api_key = get_provider_config(layer="investigation")

	if provider == "OpenAI Compatible":
		frappe.throw(
			"Investigation sessions need an Anthropic or Anthropic-Compatible "
			"provider. OpenAI-Compatible providers currently support triage only."
		)

	if base_url:
		return anthropic.Anthropic(api_key=api_key, base_url=base_url)
	return anthropic.Anthropic(api_key=api_key)


class _Usage:
	"""Duck-typed usage object so OpenAI-shaped counts flow through the same
	estimate_cost/log_usage plumbing as the Anthropic SDK's."""

	def __init__(self, input_tokens=0, output_tokens=0):
		self.input_tokens = input_tokens or 0
		self.output_tokens = output_tokens or 0


def _openai_chat(base_url, api_key, model, system_prompt, user_message, timeout=120):
	"""Minimal OpenAI-compatible /chat/completions call (Poolside, Qwen, ...).

	Uses requests directly so we don't grow a dependency on the openai SDK.
	Returns (text, _Usage).
	"""
	import requests

	response = requests.post(
		f"{base_url}/chat/completions",
		json={
			"model": model,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_message},
			],
		},
		headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
		timeout=timeout,
	)
	response.raise_for_status()
	data = response.json()

	text = data["choices"][0]["message"]["content"] or ""
	usage = data.get("usage") or {}
	return text, _Usage(usage.get("prompt_tokens"), usage.get("completion_tokens"))


def estimate_cost(model: str, usage) -> float:
	"""Estimate cost in USD from API usage object."""
	costs = get_model_cost(model)
	input_cost = (usage.input_tokens / 1_000_000) * costs["input"]
	output_cost = (usage.output_tokens / 1_000_000) * costs["output"]
	cache_read_cost = (getattr(usage, "cache_read_input_tokens", 0) / 1_000_000) * costs["cache_read"]
	cache_write_cost = (getattr(usage, "cache_creation_input_tokens", 0) / 1_000_000) * costs["cache_write"]
	return round(input_cost + output_cost + cache_read_cost + cache_write_cost, 6)


def log_usage(model: str, usage, session_name: str | None = None, ticket_name: str | None = None):
	"""Log API usage to HDS AI Usage Log."""
	try:
		frappe.get_doc(
			{
				"doctype": "HDS AI Usage Log",
				"session": session_name,
				"ticket": ticket_name,
				"model": model,
				"input_tokens": usage.input_tokens,
				"output_tokens": usage.output_tokens,
				"cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
				"cache_write_tokens": getattr(usage, "cache_creation_input_tokens", 0),
				"estimated_cost_usd": estimate_cost(model, usage),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error("Failed to log AI usage")


def call_haiku(system_prompt, user_message, ticket_name=None):
	"""Call Haiku for triage. Returns parsed JSON response.

	Args:
		system_prompt: The system prompt with triage instructions
		user_message: The ticket content to triage
		ticket_name: Optional ticket name for usage logging

	Returns:
		dict with keys: response (parsed JSON), usage (token counts), cost (USD)
	"""
	haiku_model, _ = get_models()
	provider, base_url, api_key = get_provider_config()

	if provider == "OpenAI Compatible":
		text, usage = _openai_chat(base_url, api_key, haiku_model, system_prompt, user_message)
	else:
		client = get_client()
		response = client.messages.create(
			model=haiku_model,
			max_tokens=1024,
			system=[
				{
					"type": "text",
					"text": system_prompt,
					"cache_control": {"type": "ephemeral"},
				}
			],
			messages=[{"role": "user", "content": user_message}],
		)
		text = response.content[0].text
		usage = response.usage

	log_usage(haiku_model, usage, ticket_name=ticket_name)

	# Parse JSON from response
	try:
		parsed = json.loads(text)
	except json.JSONDecodeError:
		# Try to extract JSON from markdown code block
		if "```json" in text:
			json_str = text.split("```json")[1].split("```")[0].strip()
			parsed = json.loads(json_str)
		elif "```" in text:
			json_str = text.split("```")[1].split("```")[0].strip()
			parsed = json.loads(json_str)
		else:
			parsed = {"raw_response": text, "parse_error": True}

	return {
		"response": parsed,
		"usage": {
			"input_tokens": usage.input_tokens,
			"output_tokens": usage.output_tokens,
			"cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0),
			"cache_write_tokens": getattr(usage, "cache_creation_input_tokens", 0),
		},
		"cost": estimate_cost(haiku_model, usage),
	}


def create_investigation_session(
	system_prompt,
	tools,
	initial_messages,
	model=None,
) -> tuple[anthropic.Anthropic, object]:
	"""Create an investigation session with Sonnet.

	Args:
		system_prompt: The investigation system prompt
		tools: List of tool definitions for the model
		initial_messages: Initial conversation messages
		model: Model to use (default Sonnet)

	Returns:
		Tuple of (client, initial_response)
	"""
	client = get_client()
	if not model:
		_, model = get_models()

	response = client.messages.create(
		model=model,
		max_tokens=4096,
		system=[
			{
				"type": "text",
				"text": system_prompt,
				"cache_control": {"type": "ephemeral"},
			}
		],
		tools=tools,
		messages=initial_messages,
	)

	return client, response


def continue_investigation(
	client,
	model,
	system_prompt,
	tools,
	messages,
):
	"""Continue an investigation with tool results.

	Args:
		client: Anthropic client
		model: Model ID
		system_prompt: System prompt (cached)
		tools: Tool definitions
		messages: Full conversation including tool results

	Returns:
		API response
	"""
	return client.messages.create(
		model=model,
		max_tokens=4096,
		system=[
			{
				"type": "text",
				"text": system_prompt,
				"cache_control": {"type": "ephemeral"},
			}
		],
		tools=tools,
		messages=messages,
	)
