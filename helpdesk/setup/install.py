from datetime import datetime

import frappe
from frappe.permissions import add_permission

from .default_template import create_default_template
from .file import create_helpdesk_folder
from .ticket_feedback import create_ticket_feedback_options
from .ticket_type import create_fallback_ticket_type, create_ootb_ticket_types
from .welcome_ticket import create_welcome_ticket


def before_install():
	add_support_redirect_to_tickets()


def after_install():
	add_default_categories_and_articles()
	add_default_ticket_priorities()
	add_default_sla()
	add_default_agent_groups()
	update_agent_role_permissions()
	add_default_assignment_rule()
	add_system_preset_filters()
	create_default_template()
	create_fallback_ticket_type()
	create_helpdesk_folder()
	create_ootb_ticket_types()
	create_welcome_ticket()
	create_ticket_feedback_options()


def add_support_redirect_to_tickets():
	website_settings = frappe.get_doc("Website Settings")

	for route_redirects in website_settings.route_redirects:
		if route_redirects.source == "support":
			return

	website_settings.append(
		"route_redirects",
		{
			"source": "support",
			"target": "support/tickets",
			"redirect_http_status": 301,
		},
	)
	website_settings.save()


def add_default_categories_and_articles():
	category = frappe.get_doc(
		{
			"doctype": "HD Article Category",
			"category_name": "Getting Started",
			"description": "Content for your Category",
		}
	).insert()

	frappe.get_doc(
		{
			"doctype": "HD Article",
			"title": "Introduction",
			"content": "Content for your Article",
			"category": category.name,
			"published": False,
		}
	).insert()


def add_default_sla():

	add_default_ticket_priorities()
	add_default_holidy_list()
	enable_track_service_level_agreement_in_support_settings()

	sla_doc = frappe.new_doc("HD Service Level Agreement")

	sla_doc.service_level = "Default"
	sla_doc.document_type = "HD Ticket"
	sla_doc.default_sla = 1
	sla_doc.enabled = 1

	low_priority = frappe.get_doc(
		{
			"doctype": "HD Service Level Priority",
			"default_priority": 0,
			"priority": "Low",
			"response_time": 60 * 60 * 24,
			"resolution_time": 60 * 60 * 72,
		}
	)

	medium_priority = frappe.get_doc(
		{
			"doctype": "HD Service Level Priority",
			"default_priority": 1,
			"priority": "Medium",
			"response_time": 60 * 60 * 8,
			"resolution_time": 60 * 60 * 24,
		}
	)

	high_priority = frappe.get_doc(
		{
			"doctype": "HD Service Level Priority",
			"default_priority": 0,
			"priority": "High",
			"response_time": 60 * 60 * 1,
			"resolution_time": 60 * 60 * 4,
		}
	)

	urgent_priority = frappe.get_doc(
		{
			"doctype": "HD Service Level Priority",
			"default_priority": 0,
			"priority": "Urgent",
			"response_time": 60 * 30,
			"resolution_time": 60 * 60 * 2,
		}
	)

	sla_doc.append("priorities", low_priority)
	sla_doc.append("priorities", medium_priority)
	sla_doc.append("priorities", high_priority)
	sla_doc.append("priorities", urgent_priority)

	sla_fullfilled_on_resolved = frappe.get_doc(
		{
			"doctype": "HD Service Level Agreement Fulfilled On Status",
			"status": "Resolved",
		}
	)

	sla_fullfilled_on_closed = frappe.get_doc(
		{
			"doctype": "HD Service Level Agreement Fulfilled On Status",
			"status": "Closed",
		}
	)

	sla_doc.append("sla_fulfilled_on", sla_fullfilled_on_resolved)
	sla_doc.append("sla_fulfilled_on", sla_fullfilled_on_closed)

	sla_paused_on_replied = frappe.get_doc(
		{"doctype": "HD Pause Service Level Agreement On Status", "status": "Replied"}
	)

	sla_doc.append("pause_sla_on", sla_paused_on_replied)

	sla_doc.holiday_list = "Default"

	for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
		service_day = frappe.get_doc(
			{
				"doctype": "HD Service Day",
				"workday": day,
				"start_time": "10:00:00",
				"end_time": "18:00:00",
			}
		)
		sla_doc.append("support_and_resolution", service_day)

	sla_doc.insert()


def add_default_holidy_list():
	frappe.get_doc(
		{
			"doctype": "HD Service Holiday List",
			"holiday_list_name": "Default",
			"from_date": datetime.strptime(f"Jan 1 {datetime.now().year}", "%b %d %Y"),
			"to_date": datetime.strptime(
				f"Jan 1 {datetime.now().year + 1}", "%b %d %Y"
			),
		}
	).insert()

	frappe.db.commit()


def enable_track_service_level_agreement_in_support_settings():
	support_settings = frappe.get_doc("HD Settings")
	support_settings.track_service_level_agreement = True
	support_settings.save()
	frappe.db.commit()


def add_default_ticket_priorities():
	ticket_priorities = {
		"Urgent": 100,
		"High": 200,
		"Medium": 300,
		"Low": 400,
	}

	for priority in ticket_priorities:
		if frappe.db.exists("HD Ticket Priority", priority):
			continue

		doc = frappe.new_doc("HD Ticket Priority")
		doc.name = priority
		doc.integer_value = ticket_priorities[priority]
		doc.insert()


def add_default_agent_groups():
	agent_groups = ["Billing", "Product Experts"]

	for agent_group in agent_groups:
		if not frappe.db.exists("HD Team", agent_group):
			agent_group_doc = frappe.new_doc("HD Team")
			agent_group_doc.team_name = agent_group
			agent_group_doc.insert()


def update_agent_role_permissions():
	if frappe.db.exists("Role", "Agent"):
		agent_role_doc = frappe.get_doc("Role", "Agent")
		agent_role_doc.search_bar = True
		agent_role_doc.notifications = True
		agent_role_doc.list_sidebar = True
		agent_role_doc.bulk_actions = True
		agent_role_doc.view_switcher = True
		agent_role_doc.form_sidebar = True
		agent_role_doc.form_sidebar = True
		agent_role_doc.timeline = True
		agent_role_doc.dashboard = True
		agent_role_doc.save()

		add_permission("File", "Agent", 0)
		add_permission("Contact", "Agent", 0)
		add_permission("Email Account", "Agent", 0)


def add_default_assignment_rule():
	support_settings = frappe.get_doc("HD Settings")
	support_settings.create_base_support_rotation()


def add_system_preset_filters():
	preset_filters = []
	for status in ["Closed", "Resolved", "Replied", "Open"]:
		preset_filters.append(
			{
				"doctype": "HD Preset Filter",
				"title": f"My {status} Tickets",
				"reference_doctype": "HD Ticket",
				"filters": [
					{
						"label": "Assigned To",
						"fieldname": "_assign",
						"filter_type": "is",
						"value": "@me",
					},
					{
						"label": "Status",
						"fieldname": "status",
						"filter_type": "is",
						"value": status,
					},
				],
			}
		)
	preset_filters.append(
		{
			"doctype": "HD Preset Filter",
			"title": "All Tickets",
			"reference_doctype": "HD Ticket",
			"filters": [],
		}
	)
	for preset in preset_filters:
		preset_filter_doc = frappe.get_doc(preset)
		preset_filter_doc.insert()
