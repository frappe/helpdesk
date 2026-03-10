<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Pending Invites'),
    }"
    @close="confirmingRevoke = null"
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

            <div class="relative h-7 min-w-[9rem] overflow-hidden">
              <Transition name="invite-row" mode="out-in">
                <div
                  v-if="confirmingRevoke !== invite.name"
                  key="action"
                  class="absolute inset-0 flex items-center justify-end"
                >
                  <Button
                    variant="ghost"
                    icon="trash-2"
                    :tooltip="__('Revoke Invite')"
                    @click="confirmingRevoke = invite.name"
                  />
                </div>
                <div
                  v-else
                  key="confirm"
                  class="absolute inset-0 flex items-center justify-end gap-2"
                >
                  <Button
                    variant="subtle"
                    theme="red"
                    :label="__('Confirm')"
                    :loading="cancelInviteResource.loading"
                    @click="revokeInvite(invite.name)"
                  />
                </div>
              </Transition>
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
.invite-row-enter-from {
  opacity: 0;
  transform: translateX(8px);
}

.invite-row-enter-active,
.invite-row-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.invite-row-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
</style>
