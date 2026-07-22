<template>
  <div
    class="invite-revoke-button"
    :class="{ 'invite-revoke-button--expanded': confirming }"
  >
    <Button
      :variant="confirming ? 'subtle' : 'ghost'"
      :theme="confirming ? 'red' : 'gray'"
      :icon="!confirming && 'trash-2'"
      :icon-left="confirming && 'trash-2'"
      :label="confirming && __('Confirm')"
      :tooltip="__('Revoke Invite')"
      :loading="cancelInviteResource.loading"
      class="invite-revoke-button__control"
      @click="confirming ? revoke() : (confirming = true)"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { getErrorMessage } from "@/utils";
import { Button, createResource, toast } from "frappe-ui";
import { ref } from "vue";

const props = defineProps<{
  inviteName: string;
}>();

const emit = defineEmits<{
  revoked: [];
}>();

const confirming = ref(false);

const cancelInviteResource = createResource({
  url: "frappe.core.api.user_invitation.cancel_invitation",
  method: "PATCH",
  onSuccess() {
    toast.success(__("Invitation cancelled successfully"));
    confirming.value = false;
    emit("revoked");
  },
  onError(error: any) {
    confirming.value = false;
    getErrorMessage(error, true);
  },
});

function revoke() {
  cancelInviteResource.submit({ name: props.inviteName, app_name: "helpdesk" });
}
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
