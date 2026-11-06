<template>
  <SettingsLayoutBase
    :title="__('Invite Agents')"
    :description="__('Easily invite new agents, managers, or admins.')"
  >
    <template #content>
      <form @submit.prevent="onSubmit" class="flex flex-col gap-5">
        <FormControl
          type="textarea"
          :required="true"
          :label="__('Invite by email')"
          placeholder="user1@example.com, user2@example.com, ..."
          v-model="emails"
          :debounce="100"
          :description="__('Comma separated emails to invite.')"
        />
        <div class="space-y-1.5">
          <label class="block text-base text-ink-gray-5">
            {{ __("Role") }}
            <span class="text-ink-red-6 select-none" aria-hidden="true">*</span>
          </label>
          <Select :options="roleOptions" v-model="role" required class="w-full">
            <template #suffix>
              <LucideChevronDown
                class="size-4 shrink-0 text-ink-gray-4 ms-auto"
              />
            </template>
          </Select>
          <p class="text-p-xs text-ink-gray-5">{{ roleDescription }}</p>
        </div>
        <Button
          type="submit"
          variant="solid"
          class="w-fit mt-1"
          :disabled="cancelInviteResource.loading"
          :loading="inviteByEmailResource.loading"
          >{{ __("Send Invites") }}</Button
        >
      </form>
      <template v-if="pendingInvitesResource.data?.length">
        <h2 class="mt-8 text-base-semibold">
          {{ __("Pending Invites") }}
        </h2>
        <ul class="flex flex-col gap-[0.375rem] mt-3">
          <li
            v-for="invite in pendingInvitesResource.data"
            :key="invite.name"
            class="flex items-center justify-between px-3 py-1 rounded-6 bg-surface-gray-2"
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
                :text="__('Cancel Invitation')"
              >
                <div>
                  <Button
                    icon="lucide-x"
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
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import {
  getInviteByEmailRoles,
  getInviteRoleOptions,
  roleToLabel,
  type Role,
} from "@/components/Settings/inviteRoles";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { handleInviteUserSuccess } from "@/utils";
import {
  Button,
  FormControl,
  Select,
  Tooltip,
  createResource,
  toast,
} from "frappe-ui";
import { useOnboarding } from "@framework/ui";
import { computed, ref } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";

const authStore = useAuthStore();

// @ts-expect-error
const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};

const emails = ref("");

const roleOptions = getInviteRoleOptions(authStore);
const role = ref(roleOptions[0].value);

const roleDescription = computed(
  () =>
    roleOptions.find((roleOption) => roleOption.value === role.value)!
      .description
);

const onSubmit = async () => {
  if (emails.value.trim() === "") {
    toast.error(__("Please enter at least one valid email to send an invite."));
    return;
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
    handleInviteUserSuccess(data);
    pendingInvitesResource.reload();
    updateOnboardingStep?.("invite_agents");
    capture("agents_invited", {
      data: {
        role: role.value,
      },
    });
  },
});

const pendingInvitesResource = createResource({
  url: "frappe.core.api.user_invitation.get_pending_invitations",
  params: {
    app_name: "helpdesk",
  },
  auto: true,
  method: "GET",
  transform: (data) =>
    data.filter((invite) =>
      invite.roles.some((role) =>
        ["Agent", "Agent Manager", "System Manager"].includes(role)
      )
    ),
});

const cancelInviteResource = createResource({
  url: "frappe.core.api.user_invitation.cancel_invitation",
  method: "PATCH",
  onSuccess() {
    toast.success(__("Invitation cancelled successfully"));
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
</script>

<style scoped></style>
