<template>
  <!--
    titleHeadingLvl
    description
    invitees
    existingEmails
    roles
    roleMap
    selectedRole
  -->
  <InvitationsSection
    title="Send invites to"
    :titleHeadingLvl="1"
    description="Invite users to access Helpdesk. Specify their roles to control access and permissions"
    sendInvitesBtnLabel="Send invites"
    v-model:invitees="invitees"
    inviteByEmailInputLabel="Invite by email"
    :existingEmails="(users.data ?? []).map((user: Record<'email', string>) => user.email)"
    :existingEmailInviteesMsg="
      (emails) =>
        `User${emails.length > 0 ? 's' : ''} with email ${emails.join(
          ', '
        )} already exists`
    "
    :pendingInviteesMsg="
      (emails) =>
        `User${emails.length > 0 ? 's' : ''} with email ${emails.join(
          ', '
        )} already invited`
    "
    inviteAsInputLabel="Invite as"
    :roles="roles"
    pendingInvitesSectionTitle="Pending Invites"
    deleteInvitationTooltipText="Delete Invitation"
    :roleMap="{
      Agent: 'Agent',
      'Agent Manager': 'Agent Manager',
      'System Manager': 'System Manager',
    }"
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

type Role = {
  value: "Agent" | "Agent Manager" | "System Manager";
  label: string;
  description: string;
};

const agentManagerRole = {
  value: "Agent Manager" as const,
  label: "Agent Manager",
  description:
    "Can manage and invite new users, and create public & private views (reports).",
};

const systemManagerRole = {
  value: "System Manager" as const,
  label: "System Manager",
  description:
    "Can manage all aspects of Helpdesk, including user management, customizations and settings.",
};

const roles: [Role, ...Role[]] = [
  {
    value: "Agent",
    label: "Agent",
    description:
      "Can work with leads and deals and create private views (reports).",
  },
];

if (isAdmin) {
  roles.push(agentManagerRole, systemManagerRole);
} else if (isManager) {
  roles.push(agentManagerRole);
}

const selectedRole = ref(roles[0].value);
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
    selectedRole.value = roles[0].value;
    pendingInvites.reload();
  },
});
</script>
