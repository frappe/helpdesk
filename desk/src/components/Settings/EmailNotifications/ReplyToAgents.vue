<template>
  <Notification
    v-model:content="content"
    :defaultContent="defaultContent"
    v-model:enabled="enabled"
    documentationLink="https://docs.frappe.io/helpdesk/email-notifications#available-variables-reply-from-contact"
    ref="compRef"
    name="reply_to_agents"
    :title="props.notification.label"
    :description="props.notification.description"
    :submitting="updateSettings.loading"
    :onBack="props.onBack"
    :onSubmit="onSubmit"
    :onGetDataSuccess="onGetDataSuccess"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
import Notification from "./Notification.vue";
import { createResource } from "frappe-ui";
import type { BaseSettings, Notification as NotificationType } from "./types";

const props = defineProps<{
  onBack: () => void;
  notification: NotificationType;
}>();

const content = ref("");
const defaultContent = ref("");
const enabled = ref(false);
const compRef = ref<InstanceType<typeof Notification>>();

const updateSettings = createResource({
  url: "helpdesk.api.settings.email_notifications.update_reply_to_agents",
  method: "PUT",
  auto: false,
  onSuccess(data: BaseSettings) {
    enabled.value = data.enabled;
    content.value = data.content;
    compRef.value.resetUnsavedChanges();
  },
});

function onSubmit() {
  return updateSettings.submit({
    enabled: enabled.value,
    content: content.value,
  });
}

function onGetDataSuccess(data: BaseSettings & { default_content: string }) {
  enabled.value = data.enabled;
  content.value = data.content;
  defaultContent.value = data.default_content;
}
</script>
