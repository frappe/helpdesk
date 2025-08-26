<template>
  <div class="px-10 pb-8 h-full overflow-y-auto">
    <form @submit.prevent="onSubmit" class="flex flex-col gap-5">
      <div class="sticky top-0 z-10 bg-white pt-8 pb-1">
        <SettingsLayoutHeader
          title="Invite Agents"
          description="Easily invite new agents, managers, or admins"
        />
      </div>
      <FormControl
        type="textarea"
        :required="true"
        label="Invite by email"
        placeholder="user1@example.com, user2@example.com, ..."
        v-model="emails"
        :debounce="100"
        description="Comma separated emails to invite"
      />
      <FormControl
        label="Role"
        type="select"
        :required="true"
        :options="roleOptions"
        v-model="role"
        :description="roleDescription"
      />
      <Button
        type="submit"
        variant="solid"
        class="w-fit mt-1"
        :disabled="cancelInviteResource.loading"
        :loading="inviteByEmailResource.loading"
        >Send Invites</Button
      >
    </form>
    <template v-if="pendingInvitesResource.data?.length">
      <h2 class="mt-8 text-base font-semibold">Pending Invites</h2>
      <ul class="flex flex-col gap-[0.375rem] mt-3">
        <li
          v-for="invite in pendingInvitesResource.data"
          :key="invite.name"
          class="flex items-center justify-between px-3 py-1 rounded-lg bg-surface-gray-2"
        >
          <div class="text-base">
            <span class="text-ink-gray-8">
              {{ invite.email }}
            </span>
            <span class="text-ink-gray-5">
              ({{ rolesToLabel(invite.roles) }})
            </span>
          </div>
          <div>
            <Tooltip
              :disabled="
                inviteByEmailResource.loading || cancelInviteResource.loading
              "
              text="Cancel Invitation"
            >
              <div>
                <Button
                  icon="x"
                  variant="ghost"
                  :loading="
                    cancelInviteResource.loading &&
                    invite.name === cancelInviteResource.params.name
                  "
                  @click="
                    () => {
                      if (
                        inviteByEmailResource.loading ||
                        cancelInviteResource.loading
                      ) {
                        return;
                      }
                      cancelInviteResource.submit({
                        name: invite.name,
                        app_name: 'helpdesk',
                      });
                    }
                  "
                  v-bind="{
                    ...((cancelInviteResource.loading &&
                      cancelInviteResource.params.name !== invite.name) ||
                    inviteByEmailResource.loading
                      ? { 'aria-disabled': true, class: 'opacity-25' }
                      : {}),
                  }"
                />
              </div>
            </Tooltip>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { FormControl, Button, Tooltip, createResource, toast } from "frappe-ui";
import { computed, ref } from "vue";
import { useOnboarding } from "frappe-ui/frappe";
import SettingsLayoutHeader from "./SettingsLayoutHeader.vue";

const authStore = useAuthStore();
const { isAdmin, isManager } = authStore;

const { updateOnboardingStep } = useOnboarding("helpdesk");

const emails = ref("");

type Role = "Agent" | "Agent Manager" | "System Manager";
type RoleOption = {
  label: string;
  value: Role;
  description: string;
};

const roleToLabel = (role: Role) => {
  switch (role) {
    case "Agent":
      return "Agent";
    case "Agent Manager":
      return "Manager";
    case "System Manager":
      return "Admin";
    default:
      const x: never = role;
      throw new Error(`Invalid role: ${x}`);
  }
};

const roleOptions: [RoleOption, ...RoleOption[]] = [
  {
    label: roleToLabel("Agent"),
    value: "Agent",
    description:
      "Can work on tickets, create custom views and manage private views.",
  },
];
const managerRoleOption: RoleOption = {
  label: roleToLabel("Agent Manager"),
  value: "Agent Manager",
  description:
    "Can invite new agents, manage tickets, create custom views and manage public views.",
};
if (isAdmin) {
  roleOptions.push(managerRoleOption, {
    label: roleToLabel("System Manager"),
    value: "System Manager",
    description: "Can manage all aspects of Helpdesk.",
  });
} else if (isManager) {
  roleOptions.push(managerRoleOption);
}
const role = ref(roleOptions[0].value);

const roleDescription = computed(
  () =>
    roleOptions.find((roleOption) => roleOption.value === role.value)!
      .description
);

const onSubmit = async () => {
  if (emails.value.trim() === "") {
    toast.error("At least one email required");
  }
  await inviteByEmailResource.submit({
    emails: emails.value,
    roles: getInviteByEmailRoles(role.value),
    redirect_to_path: "/helpdesk",
    app_name: "helpdesk",
  });
  resetInputValues();
};

const resetInputValues = () => {
  emails.value = "";
  role.value = roleOptions[0].value;
};

const emailsToStr = (emails: readonly string[]) => emails.join(", ");

const inviteByEmailResource = createResource({
  url: "frappe.core.api.user_invitation.invite_by_email",
  onSuccess(
    data: Record<
      | "disabled_user_emails"
      | "accepted_invite_emails"
      | "pending_invite_emails"
      | "invited_emails",
      string[]
    >
  ) {
    resetInputValues();
    let emailsStr = emailsToStr(data.invited_emails);
    if (emailsStr.trim() !== "") {
      toast.success(`${emailsStr} invited successfully`);
    }
    emailsStr = emailsToStr(data.disabled_user_emails);
    if (emailsStr.trim() !== "") {
      toast.info(`${emailsStr} already present and disabled`);
    }
    emailsStr = emailsToStr(data.pending_invite_emails);
    if (emailsStr.trim() !== "") {
      toast.info(`${emailsStr} already invited`);
    }
    emailsStr = emailsToStr(data.accepted_invite_emails);
    if (emailsStr.trim() !== "") {
      toast.info(`${emailsStr} already present`);
    }
    pendingInvitesResource.reload();
    updateOnboardingStep("invite_your_team");
  },
});

const pendingInvitesResource = createResource({
  url: "frappe.core.api.user_invitation.get_pending_invitations",
  params: { app_name: "helpdesk" },
  auto: true,
  method: "GET",
});

const cancelInviteResource = createResource({
  url: "frappe.core.api.user_invitation.cancel_invitation",
  method: "PATCH",
  onSuccess() {
    toast.success("Invitation cancelled successfully");
    pendingInvitesResource.fetch();
  },
});

const rolesToLabel = (roles: readonly Role[]) => {
  const rolesSt = new Set(roles);
  if (rolesSt.has("System Manager")) {
    return roleToLabel("System Manager");
  }
  if (rolesSt.has("Agent Manager")) {
    return roleToLabel("Agent Manager");
  }
  if (rolesSt.has("Agent")) {
    return roleToLabel("Agent");
  }
  throw new Error(`Invalid roles: ${roles.join(", ")}`);
};

const getInviteByEmailRoles = (selectedRole: Role) => {
  const res: Role[] = [];
  switch (selectedRole) {
    case "System Manager":
      res.push("Agent", "Agent Manager");
      break;
    case "Agent Manager":
      res.push("Agent");
      break;
    case "Agent":
      break;
    default:
      const x: never = selectedRole;
      throw new Error(`Invalid selected role: ${x}`);
  }
  res.push(selectedRole);
  return res;
};
</script>

<style scoped></style>
