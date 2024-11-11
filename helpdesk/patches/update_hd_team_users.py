import frappe


def execute():
    teams = frappe.get_all("HD Team", pluck="name")
    for team in teams:
        existing_agents = frappe.get_all(
            "HD Team Item", filters={"team": team}, pluck="parent"
        )
        team_users = frappe.get_all(
            "HD Team Member", filters={"parent": team}, pluck="user"
        )

        for agent in existing_agents:
            if agent not in team_users:
                team_doc = (
                    frappe.get_doc("HD Team", team)
                    .append("users", {"user": agent})
                    .save()
                )
                print("Agent Added")
