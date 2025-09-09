from datetime import datetime

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

from helpdesk.consts import DEFAULT_ARTICLE_CATEGORY

from .default_template import create_default_template
from .file import create_helpdesk_folder
from .ticket_feedback import create_ticket_feedback_options
from .ticket_type import create_fallback_ticket_type, create_ootb_ticket_types
from .welcome_ticket import create_welcome_ticket


def after_install():
    create_custom_fields(get_custom_fields())
    add_default_status()
    add_default_categories_and_articles()
    add_default_ticket_priorities()
    add_default_sla()
    add_default_agent_groups()
    update_agent_role_permissions()
    add_agent_manager_permissions()
    add_default_assignment_rule()
    create_default_template()
    create_fallback_ticket_type()
    create_helpdesk_folder()
    create_ootb_ticket_types()
    create_welcome_ticket()
    create_ticket_feedback_options()
    add_property_setters()
    # Always keep this at last, because sql_ddl makes the db commit
    add_fts_index()


def add_default_categories_and_articles():
    category = frappe.db.exists("HD Article Category", DEFAULT_ARTICLE_CATEGORY)
    if not category:
        category = frappe.get_doc(
            {
                "doctype": "HD Article Category",
                "category_name": DEFAULT_ARTICLE_CATEGORY,
            }
        ).insert()
        category = category.name
    # TODO: create 4 articles sharing information about helpdesk
    frappe.get_doc(
        {
            "doctype": "HD Article",
            "title": "Introduction",
            "content": "Content for your Article",
            "category": category,
            "published": False,
        }
    ).insert()


def add_default_sla():
    add_default_ticket_priorities()
    add_default_holiday_list()
    if frappe.db.exists("HD Service Level Agreement", "Default"):
        return
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


def add_default_holiday_list():
    if frappe.db.exists("HD Service Holiday List", "Default"):
        return
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
        add_permission("Communication", "Agent", 0)


def add_agent_manager_permissions():
    if not frappe.db.exists("Role", "Agent Manager"):
        return
    doc_to_permissions = {
        "Email Account": ["create", "delete", "write"],
        "File": ["create", "delete", "write"],
        "Contact": ["create", "delete", "write"],
        "Communication": ["create", "delete", "write"],
        "User Invitation": ["create", "write"],
        "Role": [],
    }
    for dt in doc_to_permissions.keys():
        # this adds read permission to the role
        add_permission(dt, "Agent Manager")
        for p in doc_to_permissions[dt]:
            update_permission_property(dt, "Agent Manager", 0, p, 1)


def add_default_assignment_rule():
    support_settings = frappe.get_doc("HD Settings")
    support_settings.create_base_support_rotation()


def add_property_setters():
    if not frappe.db.exists("Property Setter", {"name": "Contact-main-search_fields"}):
        doc = frappe.new_doc("Property Setter")
        doc.doctype_or_field = "DocType"
        doc.doc_type = "Contact"
        doc.property = "search_fields"
        doc.property_type = "Data"
        doc.value = "email_id"
        doc.insert()

    add_assignment_rule_property_setters()


def get_custom_fields():
    """Helpdesk specific custom fields that needs to be added to the Assignment Rule DocType."""
    return {
        "Assignment Rule": [
            {
                "description": "Autogenerated field by Helpdesk App",
                "fieldname": "assign_condition_json",
                "fieldtype": "Code",
                "label": "Assign Condition JSON",
                "insert_after": "assign_condition",
                "depends_on": "eval: doc.assign_condition_json",
            },
            {
                "description": "Autogenerated field by Helpdesk App",
                "fieldname": "unassign_condition_json",
                "fieldtype": "Code",
                "label": "Unassign Condition JSON",
                "insert_after": "unassign_condition",
                "depends_on": "eval: doc.unassign_condition_json",
            },
        ],
    }


def add_assignment_rule_property_setters():
    """Add a property setter to the Assignment Rule DocType for assign_condition and unassign_condition."""

    default_fields = {
        "doctype": "Property Setter",
        "doctype_or_field": "DocField",
        "doc_type": "Assignment Rule",
        "property_type": "Data",
        "is_system_generated": 1,
    }

    if not frappe.db.exists(
        "Property Setter", {"name": "Assignment Rule-assign_condition-depends_on"}
    ):
        frappe.get_doc(
            {
                **default_fields,
                "name": "Assignment Rule-assign_condition-depends_on",
                "field_name": "assign_condition",
                "property": "depends_on",
                "value": "eval: !doc.assign_condition_json",
            }
        ).insert()
    else:
        frappe.db.set_value(
            "Property Setter",
            {"name": "Assignment Rule-assign_condition-depends_on"},
            "value",
            "eval: !doc.assign_condition_json",
        )
    if not frappe.db.exists(
        "Property Setter", {"name": "Assignment Rule-unassign_condition-depends_on"}
    ):
        frappe.get_doc(
            {
                **default_fields,
                "name": "Assignment Rule-unassign_condition-depends_on",
                "field_name": "unassign_condition",
                "property": "depends_on",
                "value": "eval: !doc.unassign_condition_json",
            }
        ).insert()
    else:
        frappe.db.set_value(
            "Property Setter",
            {"name": "Assignment Rule-unassign_condition-depends_on"},
            "value",
            "eval: !doc.unassign_condition_json",
        )


def add_default_status():
    statuses = [
        {
            "label_agent": "Open",
            "color": "Red",
            "enabled": 1,
            "category": "Open",
            "order": 1,
        },
        {
            "label_agent": "Replied",
            "color": "Blue",
            "enabled": 1,
            "category": "Paused",
            "different_view": 1,
            "label_customer": "Awaiting Response",
            "order": 2,
        },
        {
            "label_agent": "Resolved",
            "color": "Green",
            "enabled": 1,
            "category": "Resolved",
            "order": 3,
        },
        {
            "label_agent": "Closed",
            "color": "Gray",
            "enabled": 1,
            "category": "Resolved",
            "order": 4,
        },
    ]
    for status in statuses:
        if not frappe.db.exists("HD Ticket Status", status["label_agent"]):
            frappe.get_doc({"doctype": "HD Ticket Status", **status}).insert()

    frappe.db.set_single_value("HD Settings", "default_ticket_status", "Open")
    frappe.db.set_single_value("HD Settings", "ticket_reopen_status", "Open")


def add_fts_index():
    indexes = [
        {"table": "tabHD Ticket", "column": "subject", "index_name": "ft_subject"},
        {
            "table": "tabHD Ticket",
            "column": "description",
            "index_name": "ft_description",
        },
    ]

    for i in indexes:
        add_index_if_not_exists(i["table"], i["column"], i["index_name"])


def add_index_if_not_exists(table, column, index_name):
    index_exists = frappe.db.sql(
        """
        SHOW INDEX FROM `{table}` 
            WHERE Column_name = '{column}' 
            AND Index_type = 'FULLTEXT'
        """.format(
            table=table, column=column
        ),
        as_dict=True,
    )
    print("\n\n", index_exists, "\n\n")
    if index_exists:
        frappe.db.sql_ddl(
            "DROP INDEX `{index_name}` ON `{table}`".format(
                index_name=index_exists[0].Key_name, table=table
            )
        )

    frappe.db.sql_ddl(
        "ALTER TABLE `{table}` ADD FULLTEXT INDEX `{index_name}` (`{column}`)".format(
            table=table, index_name=index_name, column=column
        )
    )
