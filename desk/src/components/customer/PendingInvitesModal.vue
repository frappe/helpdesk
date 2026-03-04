<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Pending Invites'),
    }"
  >
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <h3
          class="mb-6 flex items-center justify-between text-2xl font-semibold leading-6 text-ink-gray-9"
        >
          Pending Invites
        </h3>
        <div class="flex flex-col gap-3">
          <div
            v-for="invite in pendingInvites"
            :key="invite.name"
            class="flex items-center justify-between px-3 py-2 rounded-lg border border-outline-gray-2 min-h-[56px] overflow-hidden"
          >
            <Transition name="invite-row" mode="out-in">
              <div
                v-if="confirmingRevoke !== invite.name"
                key="info"
                class="flex items-center justify-between w-full"
              >
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
                <Button
                  variant="ghost"
                  icon="x"
                  :tooltip="__('Revoke Invite')"
                  @click="confirmingRevoke = invite.name"
                />
              </div>
              <div
                v-else
                key="confirm"
                class="flex items-center justify-between w-full"
              >
                <p class="text-sm text-ink-gray-7">
                  {{ __("Revoke this invite?") }}
                </p>
                <div class="flex gap-2">
                  <Button
                    variant="ghost"
                    :label="__('Cancel')"
                    @click="confirmingRevoke = null"
                  />
                  <Button
                    variant="solid"
                    theme="red"
                    :label="__('Confirm')"
                    :loading="cancelInviteResource.loading"
                    @click="revokeInvite(invite.name)"
                  />
                </div>
              </div>
            </Transition>
          </div>
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

const show = defineModel<boolean>();

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
