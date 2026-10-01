# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""AI investigation session lifecycle with Sonnet + MCP tool loop."""

import json
import time

import frappe
from frappe.utils import now_datetime

from helpdesk.ai_engine import (
	continue_investigation,
	create_investigation_session,
	estimate_cost,
	get_models,
	log_usage,
)
from helpdesk.mcp_client import MCPClient

# Write tool names - these require approval instead of direct execution
WRITE_TOOLS = {"set_value", "set_values", "create_doc", "delete_doc", "run_doc_method", "clear_cache"}

# Default session limits (overridden by HDS Hub Settings)
MAX_TOOL_CALLS = 30
MAX_SESSION_TIME_SECONDS = 300  # 5 minutes
MAX_SESSIONS_PER_TICKET = 3

INVESTIGATION_SYSTEM_PROMPT = """You are an expert ERPNext/Frappe support engineer investigating a customer issue on their live site.

You have access to MCP tools that let you read data from the customer's ERPNext instance. Use them to investigate the issue systematically.

## Investigation Methodology
1. First understand the schema - use get_meta to understand relevant doctypes
2. Get an overview - use get_count and get_list to understand data volumes and patterns
3. Drill into specifics - use get_doc to examine specific records
4. Cross-reference - compare data across doctypes to find mismatches
5. Check reports - use execute_report for standard ERPNext reports

## Rules
- ALL queries MUST respect the investigation scope (date ranges, specific entities) provided below
- Be systematic - don't jump to conclusions without data
- Report specific findings with document names and values
- After completing your investigation steps, provide a DIAGNOSIS section with:
  - Root causes ranked by impact
  - Specific actions the customer should take
  - Whether each issue can be auto-fixed or needs manual intervention

## Write Operations
If your diagnosis concludes that specific write operations would fix the issue, you MAY call write tools
(set_value, set_values, create_doc, delete_doc, run_doc_method, clear_cache). These will NOT execute immediately -
they get queued as proposed actions for a human agent to review and approve. After proposing a write, you will
receive a "PROPOSED" confirmation and can continue proposing more actions. Describe WHY each write is needed
in your diagnosis so the agent has context when approving.

## Deep Dive Pause
This investigation may pause after initial tool calls for agent review. If you sense the budget is running out,
provide a concise interim summary as your next response: what you've learned, what you've ruled out, and what
you'd investigate next. The agent will either let you continue, give you specific guidance, or cancel the session.

## Available Tools
{tools_description}

## Investigation Scope
{scope}

## Agent Notes
{agent_notes}
"""


def start_investigation(
	ticket_id: str,
	connection_name: str,
	agent_notes: str = "",
) -> str:
	"""Start an AI investigation session for a ticket.

	Args:
		ticket_id: HD Ticket name
		connection_name: HDS Support Connection name
		agent_notes: Optional notes from the support agent

	Returns:
		HDS AI Support Session name
	"""
	# Guard: check session limit
	existing = frappe.db.count(
		"HDS AI Support Session",
		filters={"ticket": ticket_id, "status": ["in", ["Active", "Completed"]]},
	)
	if existing >= MAX_SESSIONS_PER_TICKET:
		frappe.throw(f"Maximum {MAX_SESSIONS_PER_TICKET} sessions per ticket reached")

	# Guard: check no active session
	active = frappe.db.exists(
		"HDS AI Support Session",
		{"ticket": ticket_id, "status": "Active"},
	)
	if active:
		frappe.throw(f"Active session already exists for ticket {ticket_id}: {active}")

	# Get ticket and triage data
	ticket = frappe.get_doc("HD Ticket", ticket_id)
	triage_data = json.loads(ticket.custom_triage_data or "{}") if ticket.custom_triage_data else {}

	# Get connection info
	conn = frappe.get_doc("HDS Support Connection", connection_name)

	# Create session doc
	session = frappe.get_doc(
		{
			"doctype": "HDS AI Support Session",
			"ticket": ticket_id,
			"customer_name": conn.customer_name,
			"connection": connection_name,
			"status": "Active",
			"model_used": get_models()[1],
			"agent_notes": agent_notes,
		}
	)
	session.insert(ignore_permissions=True)
	frappe.db.commit()

	# Run investigation in background
	frappe.enqueue(
		"helpdesk.session_manager.run_investigation",
		session_name=session.name,
		ticket_id=ticket_id,
		connection_name=connection_name,
		agent_notes=agent_notes,
		triage_data=triage_data,
		job_id=f"investigate-{session.name}",
		deduplicate=True,
		timeout=MAX_SESSION_TIME_SECONDS + 30,
		queue="long",
	)

	return session.name


def run_investigation(
	session_name: str,
	ticket_id: str,
	connection_name: str,
	agent_notes: str,
	triage_data: dict,
):
	"""Background job: run the Sonnet + MCP investigation loop."""
	# Read limits from Hub Settings
	try:
		from helpdesk.ai_engine import get_hub_settings

		hub_settings = get_hub_settings()
		max_tool_calls = hub_settings.max_tool_calls_per_session or MAX_TOOL_CALLS
		max_session_time = hub_settings.max_session_time_seconds or MAX_SESSION_TIME_SECONDS
		initial_tool_calls = hub_settings.initial_tool_calls or 0
	except Exception:
		max_tool_calls = MAX_TOOL_CALLS
		max_session_time = MAX_SESSION_TIME_SECONDS
		initial_tool_calls = 0

	_, sonnet_model = get_models()

	session_start = time.monotonic()
	tool_call_count = 0
	proposed_actions = []  # Collected write tool calls for approval
	total_input_tokens = 0
	total_output_tokens = 0
	total_cache_read = 0
	total_cache_write = 0
	messages = []
	mcp_logs = []

	try:
		# Connect to customer MCP
		mcp = MCPClient(connection_name)
		tools = mcp.list_tools()

		# Build tool definitions for Anthropic API
		anthropic_tools = _build_anthropic_tools(tools)

		# Build system prompt
		ticket = frappe.get_doc("HD Ticket", ticket_id)
		scope = _build_scope(triage_data)
		tools_desc = _build_tools_description(tools)

		system_prompt = INVESTIGATION_SYSTEM_PROMPT.format(
			tools_description=tools_desc,
			scope=scope,
			agent_notes=agent_notes or "None provided",
		)

		# Build initial message with ticket context
		user_message = _build_investigation_input(ticket, triage_data)
		messages = [{"role": "user", "content": user_message}]

		# Create initial request
		client, response = create_investigation_session(
			system_prompt=system_prompt,
			tools=anthropic_tools,
			initial_messages=messages,
		)

		# Track usage
		total_input_tokens += response.usage.input_tokens
		total_output_tokens += response.usage.output_tokens
		total_cache_read += getattr(response.usage, "cache_read_input_tokens", 0)
		total_cache_write += getattr(response.usage, "cache_creation_input_tokens", 0)
		log_usage(sonnet_model, response.usage, session_name=session_name, ticket_name=ticket_id)

		# Tool use loop
		paused_for_review = False
		while response.stop_reason == "tool_use":
			# Guard: tool call limit
			if tool_call_count >= max_tool_calls:
				break

			# Guard: time limit
			elapsed = time.monotonic() - session_start
			if elapsed >= max_session_time:
				break

			# Deep dive pause: stop after initial_tool_calls for agent review
			if initial_tool_calls and tool_call_count >= initial_tool_calls:
				paused_for_review = True
				break

			# Process tool calls
			tool_results = []
			messages.append({"role": "assistant", "content": response.content})

			for block in response.content:
				if block.type != "tool_use":
					continue

				tool_call_count += 1
				tool_name = block.name
				arguments = block.input

				# Intercept write tools - collect for approval, don't execute
				if tool_name in WRITE_TOOLS:
					proposed_actions.append(
						{
							"tool_name": tool_name,
							"description": _describe_write_action(tool_name, arguments),
							"arguments": arguments,
						}
					)
					tool_results.append(
						{
							"type": "tool_result",
							"tool_use_id": block.id,
							"content": (
								"PROPOSED: %s will be queued for agent approval. "
								"Continue the investigation and propose more actions if needed. "
								"The agent will review and approve/reject proposed writes at the end."
								% tool_name
							),
							"is_error": False,
						}
					)
					mcp_logs.append(
						{
							"tool_name": tool_name,
							"action_type": "Write",
							"arguments": json.dumps(arguments, default=str),
							"result_summary": "PROPOSED for approval (not executed)",
							"execution_time_ms": 0,
						}
					)
					continue

				# Read tools - execute normally via MCP
				call_start = time.monotonic()
				try:
					result = mcp.call_tool(tool_name, arguments, ticket_id=ticket_id, session_id=session_name)
					call_elapsed = round((time.monotonic() - call_start) * 1000)

					content = result.get("content", [{}])[0].get("text", "") if result.get("content") else ""
					is_error = result.get("isError", False)

					tool_results.append(
						{
							"type": "tool_result",
							"tool_use_id": block.id,
							"content": content,
							"is_error": is_error,
						}
					)

					mcp_logs.append(
						{
							"tool_name": tool_name,
							"action_type": "Read",
							"arguments": json.dumps(arguments, default=str),
							"result_summary": content[:500] if content else "",
							"execution_time_ms": call_elapsed,
						}
					)

				except Exception as e:
					tool_results.append(
						{
							"type": "tool_result",
							"tool_use_id": block.id,
							"content": f"Error: {e}",
							"is_error": True,
						}
					)

			messages.append({"role": "user", "content": tool_results})

			# Continue conversation (with rate limit retry)
			response = _call_with_retry(client, sonnet_model, system_prompt, anthropic_tools, messages)

			# Track usage
			total_input_tokens += response.usage.input_tokens
			total_output_tokens += response.usage.output_tokens
			total_cache_read += getattr(response.usage, "cache_read_input_tokens", 0)
			total_cache_write += getattr(response.usage, "cache_creation_input_tokens", 0)
			log_usage(sonnet_model, response.usage, session_name=session_name, ticket_name=ticket_id)

		# Extract diagnosis / interim findings from the last assistant response
		diagnosis = ""
		for block in response.content:
			if hasattr(block, "text"):
				diagnosis += block.text

		# Update session with results
		session = frappe.get_doc("HDS AI Support Session", session_name)
		if paused_for_review:
			session.status = "Awaiting Review"
			# Save full conversation state for resume (includes messages + proposed_actions so far)
			session.conversation_state = _serialize_state(messages, proposed_actions)
		else:
			session.status = "Completed"
		session.ended_at = now_datetime()
		session.diagnosis = diagnosis
		session.total_tool_calls = tool_call_count
		session.total_input_tokens = total_input_tokens
		session.total_output_tokens = total_output_tokens
		session.cache_read_tokens = total_cache_read
		session.cache_write_tokens = total_cache_write
		session.estimated_cost_usd = _calculate_total_cost(
			total_input_tokens, total_output_tokens, total_cache_read, total_cache_write
		)
		session.conversation_log = json.dumps(
			[{"role": m["role"], "content": str(m["content"])[:1000]} for m in messages[-10:]],
			default=str,
		)

		# Add MCP call logs
		for log in mcp_logs:
			session.append("mcp_calls", log)

		session.save(ignore_permissions=True)
		frappe.db.commit()

		# Create action request if writes were proposed (only if session completed, not paused)
		if proposed_actions and not paused_for_review:
			from helpdesk.approval import create_action_request

			ar_name = create_action_request(session_name, ticket_id, proposed_actions)
			frappe.logger().info(f"Created action request {ar_name} with {len(proposed_actions)} actions")

	except Exception as e:
		# Save partial results including MCP logs
		try:
			session = frappe.get_doc("HDS AI Support Session", session_name)
			session.status = "Failed"
			session.ended_at = now_datetime()
			session.diagnosis = f"Investigation failed: {e}"
			session.total_tool_calls = tool_call_count
			session.total_input_tokens = total_input_tokens
			session.total_output_tokens = total_output_tokens
			session.cache_read_tokens = total_cache_read
			session.cache_write_tokens = total_cache_write
			session.estimated_cost_usd = _calculate_total_cost(
				total_input_tokens, total_output_tokens, total_cache_read, total_cache_write
			)
			for log in mcp_logs:
				session.append("mcp_calls", log)
			session.save(ignore_permissions=True)
			frappe.db.commit()
		except Exception:
			# Fallback: at minimum update status
			frappe.db.set_value(
				"HDS AI Support Session",
				session_name,
				{
					"status": "Failed",
					"ended_at": now_datetime(),
					"diagnosis": f"Investigation failed: {e}",
					"total_tool_calls": tool_call_count,
				},
				update_modified=False,
			)
			frappe.db.commit()
		frappe.log_error(f"Investigation failed for session {session_name}", str(e))


def _call_with_retry(client, model, system_prompt, tools, messages, max_retries=2):
	"""Call Anthropic API with rate limit retry and backoff."""
	import anthropic as _anthropic

	for attempt in range(max_retries + 1):
		try:
			return continue_investigation(client, model, system_prompt, tools, messages)
		except _anthropic.RateLimitError:
			if attempt < max_retries:
				wait = 30 * (attempt + 1)  # 30s, 60s
				frappe.logger().warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1})")
				time.sleep(wait)
			else:
				raise


def _build_anthropic_tools(mcp_tools: list[dict]) -> list[dict]:
	"""Convert MCP tool definitions to Anthropic API format."""
	return [
		{
			"name": tool["name"],
			"description": tool["description"],
			"input_schema": tool["inputSchema"],
		}
		for tool in mcp_tools
	]


def _build_scope(triage_data: dict) -> str:
	"""Build investigation scope from triage data."""
	scope = triage_data.get("scope", {})
	parts = []

	if scope.get("period_start") and scope.get("period_end"):
		parts.append(f"Date range: {scope['period_start']} to {scope['period_end']}")
		parts.append("ALL queries MUST filter by this date range.")

	if scope.get("specific_entities"):
		parts.append(f"Focus on: {', '.join(scope['specific_entities'])}")

	if scope.get("stated_constraint"):
		parts.append(f'Customer stated: "{scope["stated_constraint"]}"')

	if not parts:
		parts.append("No specific scope constraints. Investigate broadly but efficiently.")

	return "\n".join(parts)


def _build_tools_description(tools: list[dict]) -> str:
	"""Build a readable description of available tools."""
	lines = []
	for tool in tools:
		lines.append(f"- {tool['name']}: {tool['description']}")
	return "\n".join(lines)


def _build_investigation_input(ticket, triage_data: dict) -> str:
	"""Build the initial investigation message."""
	parts = [
		f"# Ticket #{ticket.name}: {ticket.subject}",
		"",
	]

	if ticket.description:
		desc = frappe.utils.strip_html_tags(ticket.description)
		parts.append(f"## Customer Description\n{desc}")
		parts.append("")

	# Include triage results
	if triage_data:
		parts.append("## Triage Analysis")
		if triage_data.get("category"):
			parts.append(f"- Category: {triage_data['category']}")
		if triage_data.get("priority"):
			parts.append(f"- Priority: {triage_data['priority']}")
		if triage_data.get("summary"):
			parts.append(f"- Summary: {triage_data['summary']}")
		if triage_data.get("key_doctypes"):
			parts.append(f"- Key DocTypes: {', '.join(triage_data['key_doctypes'])}")
		if triage_data.get("investigation_steps"):
			parts.append("- Investigation steps:")
			for step in triage_data["investigation_steps"]:
				parts.append(f"  {step}")
		parts.append("")

	parts.append(
		"## Task\nInvestigate this issue using the available MCP tools. Follow the investigation methodology. Report your findings with specific data."
	)

	return "\n".join(parts)


def _calculate_total_cost(input_tokens, output_tokens, cache_read, cache_write) -> float:
	"""Calculate total session cost."""
	from helpdesk.ai_engine import get_model_cost

	_, sonnet = get_models()
	costs = get_model_cost(sonnet)
	return round(
		(input_tokens / 1_000_000) * costs["input"]
		+ (output_tokens / 1_000_000) * costs["output"]
		+ (cache_read / 1_000_000) * costs["cache_read"]
		+ (cache_write / 1_000_000) * costs["cache_write"],
		6,
	)


def _describe_write_action(tool_name, arguments):
	"""Build a human-readable description of a proposed write action."""
	doctype = arguments.get("doctype", "")
	name = arguments.get("name", "")

	if tool_name == "set_value":
		return "Set %s on %s '%s' to '%s'" % (
			arguments.get("fieldname", ""),
			doctype,
			name,
			arguments.get("value", ""),
		)
	elif tool_name == "set_values":
		fields = list((arguments.get("values") or {}).keys())
		return "Update %s '%s' fields: %s" % (doctype, name, ", ".join(fields))
	elif tool_name == "create_doc":
		return "Create new %s" % doctype
	elif tool_name == "delete_doc":
		return "DELETE %s '%s'" % (doctype, name)
	elif tool_name == "run_doc_method":
		return "Call method '%s' on %s '%s'" % (arguments.get("method", ""), doctype, name)
	elif tool_name == "clear_cache":
		return "Clear site cache"
	return "%s on %s '%s'" % (tool_name, doctype, name)


def _serialize_state(messages, proposed_actions):
	"""Serialize conversation state to JSON for pause/resume.

	Anthropic message blocks (e.g. ToolUseBlock) aren't JSON-serializable directly,
	so we convert them to dicts.
	"""

	def _block_to_dict(block):
		if hasattr(block, "model_dump"):
			return block.model_dump()
		if hasattr(block, "to_dict"):
			return block.to_dict()
		if isinstance(block, dict):
			return block
		# Fallback: pull common attrs
		d = {"type": getattr(block, "type", None)}
		for attr in ("text", "id", "name", "input", "tool_use_id", "content", "is_error"):
			if hasattr(block, attr):
				d[attr] = getattr(block, attr)
		return d

	safe_messages = []
	for m in messages:
		content = m.get("content")
		if isinstance(content, list):
			content = [_block_to_dict(b) for b in content]
		safe_messages.append({"role": m["role"], "content": content})

	return json.dumps(
		{
			"messages": safe_messages,
			"proposed_actions": proposed_actions,
		},
		default=str,
	)


def _deserialize_state(state_json):
	"""Parse serialized conversation state."""
	if not state_json:
		return [], []
	try:
		data = json.loads(state_json)
	except (ValueError, TypeError):
		return [], []
	return data.get("messages", []), data.get("proposed_actions", [])


def resume_investigation(session_name, agent_guidance=""):
	"""Resume a paused investigation session.

	Appends agent_guidance to the conversation as a user message and continues
	the Sonnet loop from where it stopped.
	"""
	session = frappe.get_doc("HDS AI Support Session", session_name)
	if session.status != "Awaiting Review":
		frappe.throw("Session is not awaiting review (current status: %s)" % session.status)

	messages, proposed_actions = _deserialize_state(session.conversation_state)
	if not messages:
		frappe.throw("No saved conversation state to resume from")

	# Append agent guidance as a new user message
	guidance_text = (
		agent_guidance.strip()
		if agent_guidance
		else "Please continue the investigation based on your initial findings."
	)
	messages.append(
		{
			"role": "user",
			"content": "[AGENT GUIDANCE] %s\n\nBased on your initial findings above and this guidance, please continue the investigation."
			% guidance_text,
		}
	)

	# Reset session state
	session.status = "Active"
	session.ended_at = None
	session.conversation_state = ""
	session.save(ignore_permissions=True)
	frappe.db.commit()

	# Enqueue resume job
	frappe.enqueue(
		"helpdesk.session_manager.run_investigation_resume",
		session_name=session_name,
		messages=messages,
		proposed_actions=proposed_actions,
		agent_guidance=guidance_text,
		job_id="investigate-resume-%s" % session_name,
		deduplicate=True,
		timeout=MAX_SESSION_TIME_SECONDS + 30,
		queue="long",
	)

	return session_name


def run_investigation_resume(session_name, messages, proposed_actions, agent_guidance=""):
	"""Background: resume a previously-paused investigation."""
	session = frappe.get_doc("HDS AI Support Session", session_name)
	ticket_id = session.ticket
	connection_name = session.connection

	try:
		from helpdesk.ai_engine import get_hub_settings

		hub_settings = get_hub_settings()
		max_tool_calls = hub_settings.max_tool_calls_per_session or MAX_TOOL_CALLS
		max_session_time = hub_settings.max_session_time_seconds or MAX_SESSION_TIME_SECONDS
	except Exception:
		max_tool_calls = MAX_TOOL_CALLS
		max_session_time = MAX_SESSION_TIME_SECONDS

	_, sonnet_model = get_models()

	session_start = time.monotonic()
	tool_call_count = session.total_tool_calls or 0
	total_input_tokens = session.total_input_tokens or 0
	total_output_tokens = session.total_output_tokens or 0
	total_cache_read = session.cache_read_tokens or 0
	total_cache_write = session.cache_write_tokens or 0
	mcp_logs = []

	try:
		from helpdesk.ai_engine import get_client

		mcp = MCPClient(connection_name)
		tools = mcp.list_tools()
		anthropic_tools = _build_anthropic_tools(tools)

		ticket = frappe.get_doc("HD Ticket", ticket_id)
		triage_data = json.loads(ticket.custom_triage_data or "{}") if ticket.custom_triage_data else {}
		scope = _build_scope(triage_data)
		tools_desc = _build_tools_description(tools)
		system_prompt = INVESTIGATION_SYSTEM_PROMPT.format(
			tools_description=tools_desc,
			scope=scope,
			agent_notes=(session.agent_notes or "") + "\n\n[RESUME GUIDANCE]\n" + agent_guidance,
		)

		client = get_client()
		response = _call_with_retry(client, sonnet_model, system_prompt, anthropic_tools, messages)
		total_input_tokens += response.usage.input_tokens
		total_output_tokens += response.usage.output_tokens
		total_cache_read += getattr(response.usage, "cache_read_input_tokens", 0)
		total_cache_write += getattr(response.usage, "cache_creation_input_tokens", 0)
		log_usage(sonnet_model, response.usage, session_name=session_name, ticket_name=ticket_id)

		# Continue tool loop (no deep-dive pause on resume - agent already approved)
		while response.stop_reason == "tool_use":
			if tool_call_count >= max_tool_calls:
				break
			elapsed = time.monotonic() - session_start
			if elapsed >= max_session_time:
				break

			tool_results = []
			messages.append({"role": "assistant", "content": response.content})
			for block in response.content:
				if block.type != "tool_use":
					continue
				tool_call_count += 1
				tool_name = block.name
				arguments = block.input

				if tool_name in WRITE_TOOLS:
					proposed_actions.append(
						{
							"tool_name": tool_name,
							"description": _describe_write_action(tool_name, arguments),
							"arguments": arguments,
						}
					)
					tool_results.append(
						{
							"type": "tool_result",
							"tool_use_id": block.id,
							"content": "PROPOSED for approval. Continue investigation.",
							"is_error": False,
						}
					)
					mcp_logs.append(
						{
							"tool_name": tool_name,
							"action_type": "Write",
							"arguments": json.dumps(arguments, default=str),
							"result_summary": "PROPOSED for approval",
							"execution_time_ms": 0,
						}
					)
					continue

				call_start = time.monotonic()
				try:
					result = mcp.call_tool(tool_name, arguments, ticket_id=ticket_id, session_id=session_name)
					call_elapsed = round((time.monotonic() - call_start) * 1000)
					content = result.get("content", [{}])[0].get("text", "") if result.get("content") else ""
					tool_results.append(
						{
							"type": "tool_result",
							"tool_use_id": block.id,
							"content": content,
							"is_error": result.get("isError", False),
						}
					)
					mcp_logs.append(
						{
							"tool_name": tool_name,
							"action_type": "Read",
							"arguments": json.dumps(arguments, default=str),
							"result_summary": content[:500] if content else "",
							"execution_time_ms": call_elapsed,
						}
					)
				except Exception as e:
					tool_results.append(
						{
							"type": "tool_result",
							"tool_use_id": block.id,
							"content": "Error: %s" % e,
							"is_error": True,
						}
					)

			messages.append({"role": "user", "content": tool_results})
			response = _call_with_retry(client, sonnet_model, system_prompt, anthropic_tools, messages)
			total_input_tokens += response.usage.input_tokens
			total_output_tokens += response.usage.output_tokens
			total_cache_read += getattr(response.usage, "cache_read_input_tokens", 0)
			total_cache_write += getattr(response.usage, "cache_creation_input_tokens", 0)
			log_usage(sonnet_model, response.usage, session_name=session_name, ticket_name=ticket_id)

		# Extract diagnosis
		diagnosis = ""
		for block in response.content:
			if hasattr(block, "text"):
				diagnosis += block.text

		# Save session
		session.reload()
		session.status = "Completed"
		session.ended_at = now_datetime()
		session.diagnosis = (
			(session.diagnosis or "") + "\n\n---\n\n## Continued Investigation\n\n" + diagnosis
		)
		session.total_tool_calls = tool_call_count
		session.total_input_tokens = total_input_tokens
		session.total_output_tokens = total_output_tokens
		session.cache_read_tokens = total_cache_read
		session.cache_write_tokens = total_cache_write
		session.estimated_cost_usd = _calculate_total_cost(
			total_input_tokens, total_output_tokens, total_cache_read, total_cache_write
		)
		session.conversation_state = ""
		for log in mcp_logs:
			session.append("mcp_calls", log)
		session.save(ignore_permissions=True)
		frappe.db.commit()

		if proposed_actions:
			from helpdesk.approval import create_action_request

			create_action_request(session_name, ticket_id, proposed_actions)

	except Exception as e:
		frappe.db.set_value(
			"HDS AI Support Session",
			session_name,
			{
				"status": "Failed",
				"ended_at": now_datetime(),
				"diagnosis": (session.diagnosis or "") + "\n\nResume failed: " + str(e),
			},
			update_modified=False,
		)
		frappe.db.commit()
		frappe.log_error("Investigation resume failed for %s" % session_name, str(e))
