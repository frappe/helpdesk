<template>
  <InvitationsSection
    :titleHeadingLvl="1"
    description="Invite users to access Helpdesk. Specify their roles to control access and permissions"
    v-model:invitees="invitees"
    :existingEmails="(users.data ?? []).map((user: Record<'email', string>) => user.email)"
    :roleOptions="roleOptions"
    :roleToLabel="roleToLabel"
    v-model:selectedRole="selectedRole"
    :inviteByEmailResource="inviteByEmail"
    :pendingInvitesResource="pendingInvites"
    :errorMsg="errorMsg"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createResource, createListResource } from "frappe-ui";
import InvitationsSection from "./InvitationsSection.vue";
import { useUserStore } from "@/stores/user";
import { useAuthStore } from "@/stores/auth";
// @ts-expect-error: missing module declaration file
import { useOnboarding } from "frappe-ui/frappe";
import { z } from "zod";
import { getEmailsErrorMsg } from "./helpers";

const { users } = useUserStore();
const { isManager, isAdmin } = useAuthStore();
const { updateOnboardingStep } = useOnboarding("helpdesk");

type Role = "Agent" | "Agent Manager" | "System Manager";

type RoleOption = {
  value: Role;
  description: string;
};

const roleToLabel: Record<Role, string> = {
  Agent: "Agent",
  "Agent Manager": "Agent Manager",
  "System Manager": "Admin",
};

const agentManagerRoleOption = {
  value: "Agent Manager" as const,
  description:
    "Can manage and invite new users, and create public & private views (reports).",
};

const systemManagerRoleOption = {
  value: "System Manager" as const,
  description:
    "Can manage all aspects of Helpdesk, including user management, customizations and settings.",
};

const roleOptions: [RoleOption, ...RoleOption[]] = [
  {
    value: "Agent",
    description:
      "Can work with leads and deals and create private views (reports).",
  },
];

if (isAdmin) {
  roleOptions.push(agentManagerRoleOption, systemManagerRoleOption);
} else if (isManager) {
  roleOptions.push(agentManagerRoleOption);
}

const selectedRole = ref(roleOptions[0].value);
const invitees = ref<string[]>([]);
const errorMsg = ref<string | null>(null);
const ErrorMessageSchema = z.object({ messages: z.array(z.string()) });
const EmailsSchema = z.array(z.string());
const InviteByEmailSuccessSchema = z.object({
  existing_invites: EmailsSchema,
  existing_members: EmailsSchema,
});

const pendingInvites = createListResource({
  type: "list",
  doctype: "HD Invitation",
  filters: { status: "Pending" },
  fields: ["name", "email", "role"],
  auto: true,
});

const inviteByEmail = createResource({
  url: "helpdesk.api.invitation_flow.invite_by_email",
  makeParams() {
    return {
      emails: invitees.value.join(","),
      role: selectedRole.value,
    };
  },
  onSuccess(data: unknown) {
    const res = InviteByEmailSuccessSchema.safeParse(data);
    if (
      res.success &&
      (res.data.existing_invites.length > 0 ||
        res.data.existing_members.length > 0)
    ) {
      const errorMsgs: string[] = [];
      if (res.data.existing_invites.length > 0) {
        errorMsgs.push(getEmailsErrorMsg(res.data.existing_invites, "invited"));
      }
      if (res.data.existing_members.length > 0) {
        errorMsgs.push(getEmailsErrorMsg(res.data.existing_members, "present"));
      }
      errorMsg.value = errorMsgs.join("\n");
    }
    invitees.value = [];
    selectedRole.value = roleOptions[0].value;
    pendingInvites.reload();
    updateOnboardingStep("invite_your_team");
  },
  onError(error: unknown) {
    const res = ErrorMessageSchema.safeParse(error);
    if (res.success && res.data.messages.length > 0) {
      errorMsg.value = res.data.messages[0];
      return;
    }
    console.error(error);
  },
});
</script>
