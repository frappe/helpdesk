<template>
  <form @submit.prevent="onSubmit" class="flex flex-col gap-5">
    <div class="flex flex-col gap-4">
      <h1 class="text-lg font-semibold py-[5px]">Invite Agent</h1>
      <FormControl
        type="textarea"
        label="Invite by email"
        placeholder="user1@example.com, user2@example.com, ..."
        v-model="emails"
        :debounce="100"
        description="Comma separated emails to invite"
      />
    </div>
    <FormControl
      label="Role"
      type="select"
      :options="roleOptions"
      v-model="role"
      :description="roleDescription"
    />
    <Button
      type="submit"
      variant="solid"
      class="w-fit mt-1"
      :disabled="pendingInvitesResource.delete.loading"
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
            ({{ roleToLabel(invite.role) }})
          </span>
        </div>
        <div>
          <Tooltip
            :disabled="
              pendingInvitesResource.delete.loading ||
              inviteByEmailResource.loading
            "
            text="Delete Invitation"
          >
            <!-- 
                This `div` is necessary to prevent the attached listener from getting called twice 
                (maybe a bug in frappe-ui?)
            -->
            <div>
              <Button
                icon="x"
                variant="ghost"
                @click="
                  () => {
                    if (
                      pendingInvitesResource.delete.loading ||
                      inviteByEmailResource.loading
                    ) {
                      return;
                    }
                    pendingInvitesResource.delete.submit(invite.name);
                  }
                "
                :loading="
                  pendingInvitesResource.delete.loading &&
                  pendingInvitesResource.delete.params.name === invite.name
                "
                :class="
                  pendingInvitesResource.delete.loading &&
                  pendingInvitesResource.delete.params.name !== invite.name
                    ? 'opacity-25'
                    : ''
                "
                v-bind="{
                  ...{
                    'aria-disabled':
                      pendingInvitesResource.delete.loading &&
                      pendingInvitesResource.delete.params.name !== invite.name,
                  },
                }"
              />
            </div>
          </Tooltip>
        </div>
      </li>
    </ul>
  </template>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import {
  FormControl,
  Button,
  Tooltip,
  createResource,
  createListResource,
  toast,
} from "frappe-ui";
import { computed, onMounted, ref } from "vue";
// @ts-expect-error: no declaration file
import { useOnboarding } from "frappe-ui/frappe";

const authStore: Record<"isAdmin" | "isManager", boolean> = useAuthStore();
const { isAdmin, isManager } = authStore;

const { updateOnboardingStep } = useOnboarding("helpdesk");

const emails = ref("");

type RoleOption = Record<"label" | "value" | "description", string>;
const roleOptions: [RoleOption, ...RoleOption[]] = [
  {
    label: "Agent",
    value: "Agent",
    description:
      "Can work on tickets, create custom views and manage private views.",
  },
];
const managerRoleOption: RoleOption = {
  label: "Manager",
  value: "Agent Manager",
  description:
    "Can invite new agents, manage tickets, create custom views and manage public views.",
};
if (isAdmin) {
  roleOptions.push(managerRoleOption, {
    label: "Admin",
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

const onSubmit = () => {
  if (emails.value.trim() === "") {
    toast.error("At least one email required");
    return;
  }
  inviteByEmailResource.submit();
};

const resetInputValues = () => {
  emails.value = "";
  role.value = roleOptions[0].value;
};

const emailsToStr = (emails: readonly string[]) => emails.join(", ");

const inviteByEmailResource = createResource({
  url: "frappe.core.api.user_invitation.invite_by_email",
  makeParams: () => ({
    emails: emails.value,
    role: role.value,
    redirect_to_path: "/helpdesk",
    app_name: "helpdesk",
  }),
  onSuccess(
    data: Record<
      "existing_user_emails" | "existing_invited_emails" | "invited_emails",
      string[]
    >
  ) {
    resetInputValues();
    let emailsStr = emailsToStr(data.invited_emails);
    if (emailsStr.trim() !== "") {
      toast.success(`${emailsStr} invited successfully`);
    }
    emailsStr = emailsToStr(data.existing_invited_emails);
    if (emailsStr.trim() !== "") {
      toast.info(`${emailsStr} already invited`);
    }
    emailsStr = emailsToStr(data.existing_user_emails);
    if (emailsStr.trim() !== "") {
      toast.info(`${emailsStr} already present`);
    }
    pendingInvitesResource.reload();
    updateOnboardingStep("invite_your_team");
  },
});

const pendingInvitesResource = createListResource({
  doctype: "User Invitation",
  filters: { status: "Pending" },
  fields: ["name", "email", "role"],
  auto: true,
});

const roleToLabel = (role: string) =>
  roleOptions.find((r) => r.value === role)!.label;
</script>

<style scoped></style>
