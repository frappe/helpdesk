import frappe

def before_install():
	set_home_page_to_kb()

def after_install():
	add_default_categories()
	add_default_sla()

def set_home_page_to_kb():
	website_settings = frappe.get_doc("Website Settings")

	if not website_settings.home_page:
		website_settings.home_page = '/support/kb'
		website_settings.save()

def add_support_redirect_to_tickets():
    website_settings = frappe.get_doc("Website Settings")

    for route_redirects in website_settings.route_redirects:
        if(route_redirects.source == "support"):
            return

    base_route = frappe.get_doc({
        "doctype": "Website Route Redirect",
        "source": "support" ,
        "target": "support/tickets"
    })

    website_settings.append('route_redirects', base_route)
    website_settings.save()

def add_default_categories():
	frappe.get_doc({
		"doctype": "Category",
		"category_name": "FAQ",
		"description": "Description for your FAQs",
		"is_group": True
	}).insert()

	frappe.get_doc({
		"doctype": "Category",
		"category_name": "Getting Started",
		"description": "Description for your Getting Started",
		"is_group": True
	}).insert()

def add_default_sla():

	add_default_ticket_priorities()
	add_default_holidy_list()
	enable_track_service_level_agreement_in_support_settings()

	sla_doc = frappe.new_doc("Service Level Agreement")
	
	sla_doc.service_level = "Default"
	sla_doc.document_type = "Ticket"
	sla_doc.default_service_level_agreement = 1
	sla_doc.enabled = 1

	low_priority = frappe.get_doc({
		"doctype": "Service Level Priority",
		"default_priority": 0,
		"priority": "Low",
		"response_time": 60 * 60 * 24,
		"resolution_time": 60 * 60 * 72,
	})

	medium_priority = frappe.get_doc({
		"doctype": "Service Level Priority",
		"default_priority": 1,
		"priority": "Medium",
		"response_time": 60 * 60 * 8,
		"resolution_time": 60 * 60 * 24,
	})

	high_priority = frappe.get_doc({
		"doctype": "Service Level Priority",
		"default_priority": 0,
		"priority": "High",
		"response_time": 60 * 60 * 1,
		"resolution_time": 60 * 60 * 4,
	})

	sla_doc.append("priorities", low_priority)
	sla_doc.append("priorities", medium_priority)
	sla_doc.append("priorities", high_priority)

	sla_fullfilled_on_resolved = frappe.get_doc({
		"doctype": "SLA Fulfilled On Status",
		"status": "Resolved"
	})

	sla_fullfilled_on_closed = frappe.get_doc({
		"doctype": "SLA Fulfilled On Status",
		"status": "Closed"
	})

	sla_doc.append("sla_fulfilled_on", sla_fullfilled_on_resolved)
	sla_doc.append("sla_fulfilled_on", sla_fullfilled_on_closed)

	sla_paused_on_hold = frappe.get_doc({
		"doctype": "Pause SLA On Status",
		"status": "On Hold"
	})

	sla_paused_on_replied = frappe.get_doc({
		"doctype": "Pause SLA On Status",
		"status": "Replied"
	})

	sla_doc.append("pause_sla_on", sla_paused_on_hold)
	sla_doc.append("pause_sla_on", sla_paused_on_replied)

	sla_doc.holiday_list = "Default"

	for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
		service_day = frappe.get_doc({
			"doctype": "Service Day",
			"workday": day,
			"start_time": "10:00:00",
			"end_time": "18:00:00"
		})
		sla_doc.append("support_and_resolution", service_day)

	sla_doc.insert()

def add_default_ticket_priorities():
	frappe.get_doc({
		"doctype": "Ticket Priority",
		"name": "Low"
	}).insert()

	frappe.get_doc({
		"doctype": "Ticket Priority",
		"name": "Medium"
	}).insert()

	frappe.get_doc({
		"doctype": "Ticket Priority",
		"name": "High"
	}).insert()

def add_default_holidy_list():
	from datetime import datetime
	frappe.get_doc({
		"doctype": "Service Holiday List",
		"holiday_list_name": "default",
		"from_date": datetime.strptime(f"Jan 1 {datetime.now().year}", "%b %d %Y"),
		"to_date": datetime.strptime(f"Jan 1 {datetime.now().year + 1}", "%b %d %Y"),
	}).insert()

	frappe.db.commit()

def enable_track_service_level_agreement_in_support_settings():
	support_settings = frappe.get_doc("Support Settings")
	support_settings.track_service_level_agreement = True
	support_settings.save()
	frappe.db.commit()

def add_default_ticket_template():
	template = frappe.new_doc("Ticket Template")
	
	template.template_name = "Default"
	template.append("fields", {
		'label': 'Subject',
		'fieldname': 'subject',
		'fieldtype': 'Data',
	})
	template.append("fields", {
		'label': 'Description',
		'fieldname': 'description',
		'fieldtype': 'Long Text',
	})

	template.insert()
