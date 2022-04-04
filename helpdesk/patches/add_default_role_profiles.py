from dataclasses import fields
from helpdesk.setup.install import add_default_role_profiles
import frappe

def execute():
    add_default_role_profiles()

    agents = frappe.get_all("Agent", fields=["user", "name"])
    for agent in agents:
        agent_doc = frappe.get_doc("Agent", agent.name)
        agent_doc.role = "Agent"
        agent_doc.save()

        user_doc = frappe.get_doc("User", agent.user)
        user_doc.role_profile_name = "Agent"
        user_doc.save()
