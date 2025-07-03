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
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createResource, createListResource } from "frappe-ui";
import InvitationsSection from "./InvitationsSection.vue";
import { useUserStore } from "@/stores/user";
import { useAuthStore } from "@/stores/auth";

const { users } = useUserStore();
const { isManager, isAdmin } = useAuthStore();

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
  onSuccess() {
    invitees.value = [];
    selectedRole.value = roleOptions[0].value;
    pendingInvites.reload();
  },
});
</script>
