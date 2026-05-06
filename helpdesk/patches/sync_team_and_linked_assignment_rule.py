import frappe


def execute():
    """
    Merges users from HD Team and its linked Assignment Rule (both `users` and
    `weighted_users`) so that the final state of both documents contains the
    union of all users.

    Existing weighted_users weights are preserved; new users are added with
    weight=1.
    """
    teams = frappe.get_all(
        "HD Team",
        filters={"assignment_rule": ["is", "set"]},
        fields=["name", "assignment_rule"],
    )

    for team_row in teams:
        team = frappe.get_doc("HD Team", team_row.name)
        ar = frappe.get_doc("Assignment Rule", team_row.assignment_rule)

        team_users = {u.user for u in team.users if u.user}
        ar_users = {u.user for u in ar.users if u.user}
        ar_weighted_users = {u.user for u in ar.weighted_users if u.user}

        merged = team_users | ar_users | ar_weighted_users

        if not merged:
            continue

        # --- Update Assignment Rule ---
        ar.users = []
        for user in merged:
            ar.append("users", {"user": user})

        # Preserve existing weights, add new users at weight=1
        existing_weighted = {
            row.user: row.weight for row in ar.weighted_users if row.user
        }
        ar.weighted_users = []
        for user in merged:
            ar.append(
                "weighted_users",
                {
                    "user": user,
                    "weight": existing_weighted.get(user, 1),
                },
            )

        ar.disabled = False
        ar.flags.ignore_hd_team_sync = True
        ar.save(ignore_permissions=True)

        # --- Update HD Team ---
        team.users = []
        for user in merged:
            team.append("users", {"user": user})

        team.flags.ignore_ar_sync = True
        team.save(ignore_permissions=True)

        frappe.db.commit()
