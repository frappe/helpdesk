import frappe


def execute():
    teams = frappe.get_all("HD Team", pluck="name")
    for team in teams:
        existing_agents = frappe.get_all(
            "HD Team Item", filters={"team": team}, pluck="parent"
        )  # agents in HD Agent doctype
        team_users = frappe.get_all(
            "HD Team Member", filters={"parent": team}, pluck="user"
        )  # agents in HD Team doctype

        for agent in existing_agents:
            is_agent_active = frappe.get_value("HD Agent", agent, "is_active")
            if is_agent_active and agent not in team_users:
                team_doc = (
                    frappe.get_doc("HD Team", team)
                    .append("users", {"user": agent})
                    .save()
                )
                print("Agent Added")
