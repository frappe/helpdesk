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
            class="flex items-center justify-between px-3 py-2 rounded-lg border border-outline-gray-2 bg-surface-gray-2"
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
              @click="() => revokeInvite(invite.name)"
            />
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
import { inject } from "vue";

const show = defineModel<boolean>();

interface PendingInvite {
  name: string;
  email: string;
  roles: string[];
  invited_by: string;
  invited_on: string;
}

defineProps<{
  pendingInvites: PendingInvite[];
}>();

const customer = inject(CustomerResourceSymbol)!;

const cancelInviteResource = createResource({
  url: "frappe.core.api.user_invitation.cancel_invitation",
  method: "PATCH",
  onSuccess() {
    toast.success("Invitation cancelled successfully");
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
</script>
