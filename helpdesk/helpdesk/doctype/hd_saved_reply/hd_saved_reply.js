// Copyright (c) 2022, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Saved Reply", {
  setup: async function (frm) {
    const user = await frappe.call("helpdesk.api.auth.get_user");
    const config = await frappe.call("helpdesk.api.config.get_config");
    const isTeamRestrictionApplied = Boolean(
      config.message.restrict_tickets_by_agent_group
    );
    const isGlobalScopeDisabled = Boolean(
      config.message.disable_saved_replies_global_scope
    );
    const isAdmin = user.message.is_admin;
    const userTeams = user.message.user_teams || [];

    configureGlobalScope(frm, isTeamRestrictionApplied, isGlobalScopeDisabled);

    frm.set_query("teams", () => {
      if (!isAdmin && isTeamRestrictionApplied) {
        return {
          filters: {
            name: ["in", userTeams],
          },
        };
      }
      return {};
    });
  },
  refresh: async function (frm) {
    const config = await frappe.call("helpdesk.api.config.get_config");
    const isTeamRestrictionApplied = Boolean(
      config.message.restrict_tickets_by_agent_group
    );
    const isGlobalScopeDisabled = Boolean(
      config.message.disable_saved_replies_global_scope
    );

    configureGlobalScope(frm, isTeamRestrictionApplied, isGlobalScopeDisabled);
  },
});

const configureGlobalScope = async (
  frm,
  isTeamRestrictionApplied,
  isGlobalScopeDisabled
) => {
  if (isTeamRestrictionApplied && isGlobalScopeDisabled) {
    let scopes = frm.get_docfield("scope").options;
    const _scopes = scopes.split("\n");
    scopes = _scopes.filter((scope) => scope !== "Global");
    scopes = scopes.join("\n");
    frm.set_df_property("scope", "options", scopes);
    frm.set_value("scope", "Personal");
  }
};
