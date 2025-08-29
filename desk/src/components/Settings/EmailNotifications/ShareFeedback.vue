<template>
  <Notification
    ref="compRef"
    name="share_feedback"
    :title="props.notification.label"
    :description="props.notification.description"
    v-model:content="content"
    :defaultContent="defaultContent"
    v-model:enabled="enabled"
    documentationLink="https://docs.frappe.io/helpdesk/email-notifications#available-variables-share-feedback"
    :onBack="props.onBack"
    :onSubmit="onSubmit"
    :onGetDataSuccess="onGetDataSuccess"
    :submitting="updateSettings.loading"
  >
    <template #formFields>
      <FormControl
        type="autocomplete"
        size="sm"
        :label="__('On Ticket Status')"
        :options="statusOptions"
        :required="true"
        :model-value="ticketStatus"
        @update:model-value="
          (val) => {
            ticketStatus = val;
            compRef.setUnsavedChanges();
          }
        "
      />
    </template>
  </Notification>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import Notification from "./Notification.vue";
import { createResource } from "frappe-ui";
import type { BaseSettings, Notification as NotificationType } from "./types";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";

const props = defineProps<{
  onBack: () => void;
  notification: NotificationType;
}>();

const content = ref("");
const defaultContent = ref("");
const enabled = ref(false);
const compRef = ref<InstanceType<typeof Notification>>();
const { statuses } = useTicketStatusStore();
const statusOptions = computed<Record<"label" | "value", string>[]>(() =>
  statuses.data
    .filter((s) => s.category === "Resolved")
    .map((s) => ({
      label: __(s.label_agent),
      value: s.label_agent,
    }))
);
const ticketStatus = ref<Record<"label" | "value", string> | null>(null);

type Data = {
  ticket_status: Record<"label" | "value", string>;
} & BaseSettings;

const updateSettings = createResource({
  url: "helpdesk.api.settings.email_notifications.update_share_feedback",
  method: "PUT",
  auto: false,
  onSuccess(_data: Data) {
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
  ticketStatus.value = {
    label: __(data.ticket_status.label),
    value: data.ticket_status.value,
  };
  enabled.value = data.enabled;
  content.value = data.content;
  defaultContent.value = data.default_content;
}
</script>
