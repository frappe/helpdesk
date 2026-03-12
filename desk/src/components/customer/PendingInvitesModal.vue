<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Pending Invites'),
    }"
    @after-leave="confirmingRevoke = null"
  >
    <template #body-content>
      <div class="flex flex-col">
        <div v-for="(invite, idx) in pendingInvites" :key="invite.name">
          <div class="flex items-center justify-between gap-4 py-3">
            <div>
              <div class="text-base">
                <span class="text-ink-gray-8">{{ invite.email }}</span>
                <span class="text-ink-gray-5 ml-1"
                  >({{ parseRoles(invite.roles.join(", ")) }})</span
                >
              </div>
              <p class="text-xs text-ink-gray-4 mt-0.5">
                {{ __("Invited by") }} {{ invite.invited_by }} ·
                {{ dayjsLocal(invite.invited_on).fromNow() }}
              </p>
            </div>

            <div class="flex justify-end min-w-[9rem]">
              <div
                class="invite-revoke-button"
                :class="{
                  'invite-revoke-button--expanded':
                    confirmingRevoke === invite.name,
                }"
              >
                <Button
                  :variant="
                    confirmingRevoke === invite.name ? 'subtle' : 'ghost'
                  "
                  :theme="confirmingRevoke === invite.name ? 'red' : 'gray'"
                  :icon="confirmingRevoke !== invite.name && 'trash-2'"
                  :icon-left="confirmingRevoke === invite.name && 'trash-2'"
                  :label="confirmingRevoke === invite.name && __('Confirm')"
                  :tooltip="__('Revoke Invite')"
                  :loading="cancelInviteResource.loading"
                  class="invite-revoke-button__control"
                  @click="
                    confirmingRevoke === invite.name
                      ? revokeInvite(invite.name)
                      : (confirmingRevoke = invite.name)
                  "
                />
              </div>
            </div>
          </div>
          <div
            v-if="idx !== pendingInvites.length - 1"
            class="border-t border-gray-200 w-full"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { Dialog, createResource, dayjsLocal, toast } from "frappe-ui";
import { inject, ref, watch } from "vue";

const show = defineModel<boolean>({ default: false });

interface PendingInvite {
  name: string;
  email: string;
  roles: string[];
  invited_by: string;
  invited_on: string;
}

const props = defineProps<{
  pendingInvites: PendingInvite[];
}>();

const customer = inject(CustomerResourceSymbol)!;
const confirmingRevoke = ref<string | null>(null);

const cancelInviteResource = createResource({
  url: "frappe.core.api.user_invitation.cancel_invitation",
  method: "PATCH",
  onSuccess() {
    toast.success("Invitation cancelled successfully");
    confirmingRevoke.value = null;
    customer.getPendingInvites?.reload();
  },
});

function parseRoles(roles: string) {
  // parse "System Manager, Sales User" to "System Manager and Sales User"
  //   HD Customer to Customer
  // HD Customer Manager to Customer Manager
  return roles
    .split(",")
    .map((role) =>
      role.replace("HD ", "").replace("Customer", "Customer").trim()
    )
    .join(" and ");
}

function revokeInvite(name: string) {
  cancelInviteResource.submit({ name, app_name: "helpdesk" });
}
watch(
  () => props.pendingInvites,
  (invites: PendingInvite[]) => {
    if (!cancelInviteResource.loading && !invites.length) {
      show.value = false;
    }
  }
);
</script>

<style scoped>
.invite-revoke-button {
  width: 1.75rem;
  margin-left: auto;
  overflow: hidden;
  transition: width 0.22s ease;
}

.invite-revoke-button--expanded {
  width: 6.75rem;
}

.invite-revoke-button :deep(button) {
  width: 100%;
  min-width: 100%;
  justify-content: center;
  white-space: nowrap;
  transition: background-color 0.22s ease, color 0.22s ease,
    border-color 0.22s ease;
}
</style>
