import typing

import frappe


def on_update(invitation: frappe.model.document.Document, event: typing.Any) -> None:
    if invitation.has_value_changed("status") and invitation.status == "Accepted":
        user = frappe.get_doc("User", invitation.email)
        current_roles = {data.role for data in user.get("roles")}
        agent_role = "Agent"
        agent_manager_role = "Agent Manager"
        if "System Manager" in current_roles:
            user.append_roles(agent_role, agent_manager_role)
        elif agent_manager_role:
            user.append_roles(agent_role)
        block_modules = frappe.get_all(
            "Module Def",
            fields=["name as module"],
            filters={"name": ["!=", "Helpdesk"]},
        )
        if block_modules:
            user.set("block_modules", block_modules)
        user.save(ignore_permissions=True)
        hd_agent_doctype = "HD Agent"
        if not frappe.db.exists(hd_agent_doctype, {"user": user.email}):
            frappe.get_doc(
                doctype=hd_agent_doctype,
                user=user.email,
                agent_name=user.first_name,
                is_active=True,
            ).insert(ignore_permissions=True)
