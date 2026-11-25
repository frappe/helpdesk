<template>
  <section class="space-y-8">
    <div class="space-y-1.5">
      <h1 class="text-2xl-semibold text-ink-gray-9">
        {{ __("Invite your agents") }}
      </h1>
      <p class="text-p-base text-ink-gray-6">
        {{ __("They get an email with a link to join your Helpdesk.") }}
      </p>
    </div>

    <InviteStep
      :roles="ROLE_OPTIONS"
      default-role="Agent"
      :send="send"
      :labels="labels"
      @invitees="(people) => (setup.typed = people)"
      @done="finish"
      @skip="next({ skipped: !invited.length })"
    />
  </section>
</template>

<script setup lang="ts">
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { AGENT_ROLES, type AgentRole, getInviteByEmailRoles } from "@/utils";
import { InviteStep, useOnboarding } from "@framework/ui";
import { call } from "frappe-ui";
import { normalizeEmail, useSetupFlow } from "./setup";

const { invited, next, reportError, setup } = useSetupFlow();
const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};

const ROLE_OPTIONS = AGENT_ROLES.map((role) => ({
  label: __(role),
  value: role,
}));

const labels = {
  placeholder: "name@company.com",
  email: (row: number) => __("Email {0}", [row]),
  role: (row: number) => __("Role {0}", [row]),
  remove: (row: number) => __("Remove {0}", [row]),
  add: __("Add another"),
  send: __("Send invites"),
  continue: __("Continue"),
  sent: __("Sent"),
  skip: __("Skip this step"),
  invalid: __("Enter a valid email address"),
  duplicate: __("This email is already in the list"),
  failed: __("Could not send invites"),
  failedTitle: (count: number) =>
    count === 1
      ? __("1 invite could not be sent")
      : __("{0} invites could not be sent", [count]),
  failedWho: (emails: string) =>
    __("Could not invite {0}: user is disabled.", [emails]),
};

type InviteResult = {
  invited_emails: string[];
  pending_invite_emails: string[];
  accepted_invite_emails: string[];
  disabled_user_emails: string[];
};

async function send(role: string, emails: string[]) {
  try {
    const result: InviteResult = await call(
      "frappe.core.api.user_invitation.invite_by_email",
      {
        emails: emails.map(normalizeEmail).join(","),
        roles: getInviteByEmailRoles(role as AgentRole),
        redirect_to_path: "/helpdesk",
        app_name: "helpdesk",
      }
    );
    setup.sentTo.push(
      ...result.invited_emails,
      ...result.pending_invite_emails
    );
    capture("agents_invited", { data: { role, source: "setup" } });
    return {
      invited: result.invited_emails.length,
      failed: result.disabled_user_emails,
    };
  } catch (e) {
    reportError("send_invites", e);
    throw e;
  }
}

function finish() {
  if (invited.value.length) updateOnboardingStep?.("invite_agents");
  next();
}
</script>
