<template>
  <Notification
    ref="compRef"
    name="share_feedback"
    :title="__('Share Feedback')"
    v-model:content="content"
    :defaultContent="defaultContent"
    v-model:enabled="enabled"
    :onBack="props.onBack"
    :onSubmit="onSubmit"
    :onGetDataSuccess="onGetDataSuccess"
    :submitting="updateSettings.loading"
  >
    <template #formFields>
      <FormControl
        type="select"
        size="sm"
        :label="__('On Ticket Status')"
        :options="
          ticketStatusOptions.map((option) => ({
            label: __(option),
            value: option,
          }))
        "
        :required="true"
        v-model="ticketStatus"
        :onchange="() => compRef.setUnsavedChanges()"
      />
    </template>
  </Notification>
</template>

<script setup lang="ts">
import { ref } from "vue";
import Notification from "./Notification.vue";
import { createResource } from "frappe-ui";
import type { BaseSettings } from "./types";

const props = defineProps<{ onBack: () => void }>();

const content = ref("");
const defaultContent = ref("");
const enabled = ref(false);
const ticketStatusOptions = ["Closed", "Resolved"] as const;
type TicketStatus = typeof ticketStatusOptions[number];
const ticketStatus = ref<TicketStatus>(ticketStatusOptions[0]);
const compRef = ref<InstanceType<typeof Notification>>();

type Data = {
  ticket_status: TicketStatus;
} & BaseSettings;

const updateSettings = createResource({
  url: "helpdesk.api.settings.email_notifications.update_share_feedback",
  method: "PUT",
  auto: false,
  onSuccess(data: Data) {
    ticketStatus.value = data.ticket_status;
    enabled.value = data.enabled;
    content.value = data.content;
    compRef.value.resetUnsavedChanges();
  },
});

function onSubmit() {
  return updateSettings.submit({
    ticket_status: ticketStatus.value,
    enabled: enabled.value,
    content: content.value,
  });
}

function onGetDataSuccess(data: Data & { default_content: string }) {
  ticketStatus.value = data.ticket_status;
  enabled.value = data.enabled;
  content.value = data.content;
  defaultContent.value = data.default_content;
}
</script>

<style scoped></style>
