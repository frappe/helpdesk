<template>
  <form @submit.prevent="onSubmit" class="flex-grow flex flex-col isolate">
    <!-- Header -->
    <div
      class="flex justify-between items-center gap-2 pb-8 sticky top-0 z-10 bg-white pt-8"
    >
      <div class="flex items-center gap-x-1">
        <div class="flex items-center gap-x-1">
          <button
            @click="props.onBack"
            class="relative text-ink-gray-7 active:text-ink-gray-5 -ml-4"
          >
            <span class="sr-only">{{ __("back to email event list") }}</span>
            <LucideChevronLeft />
          </button>
          <h1 class="font-semibold text-ink-gray-7 text-xl">
            {{ __("Reply Via Agent") }}
          </h1>
        </div>
        <Badge
          v-if="unsavedChanges"
          :variant="'subtle'"
          :theme="'red'"
          size="sm"
          :label="__('Not Saved')"
        />
      </div>
      <div
        :inert="getEmailEventData.loading"
        class="flex items-center gap-x-2"
        :class="{ invisible: getEmailEventData.loading }"
      >
        <Switch
          size="sm"
          :label="__('Enabled')"
          v-model="enabled"
          @update:model-value="setUnsavedChanges"
          class="flex-row-reverse gap-x-2 text-sm text-ink-gray-7 font-medium pl-0 hover:bg-transparent active:bg-transparent"
        />
        <Button
          type="submit"
          :label="__('Save')"
          theme="gray"
          variant="solid"
          :disabled="!unsavedChanges"
          :loading="setReplyViaAgentEmailSettings.loading"
        />
      </div>
    </div>
    <!-- Body -->
    <div
      class="flex flex-col gap-8 flex-grow pb-8"
      :class="{
        'items-center justify-center': getEmailEventData.loading,
      }"
    >
      <template v-if="!getEmailEventData.loading">
        <div class="flex flex-col gap-2">
          <FormControl
            type="textarea"
            size="sm"
            :label="__('Email Content')"
            :required="true"
            :rows="10"
            v-model="content"
            :oninput="setUnsavedChanges"
          />
          <Button
            type="button"
            size="sm"
            variant="subtle"
            @click="resetContent"
            class="w-fit"
          >
            {{ __("Reset Content") }}
          </Button>
        </div>
      </template>
      <LoadingIndicator v-else class="w-4" />
    </div>
  </form>
</template>

<script setup lang="ts">
import {
  Badge,
  FormControl,
  Button,
  LoadingIndicator,
  Switch,
  createResource,
} from "frappe-ui";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import type { EmailEvent } from "./types";
import { ref } from "vue";

const props = defineProps<{
  onBack: () => void;
  emailEvent: EmailEvent;
}>();

const unsavedChanges = ref(false);
const enabled = ref(false);
const content = ref("");
const defaultContent = ref("");

type EmailEventData = {
  enabled: boolean;
  email_content: string;
};

const getEmailEventData = createResource({
  url: "helpdesk.api.email_event_settings.get_event_data",
  method: "GET",
  params: {
    email_event: "reply_via_agent",
  },
  auto: true,
  onSuccess(data: EmailEventData & { default_email_content: string }) {
    enabled.value = data.enabled;
    content.value = data.email_content;
    defaultContent.value = data.default_email_content;
  },
});

const setReplyViaAgentEmailSettings = createResource({
  url: "helpdesk.api.email_event_settings.set_reply_via_agent_email_settings",
  method: "PUT",
  auto: false,
  onSuccess(data: EmailEventData) {
    enabled.value = data.enabled;
    content.value = data.email_content;
    unsavedChanges.value = false;
  },
});

function setUnsavedChanges() {
  unsavedChanges.value = true;
}

function onSubmit() {
  return setReplyViaAgentEmailSettings.submit({
    enabled: enabled.value,
    email_content: content.value,
  });
}

function resetContent() {
  if (content.value === defaultContent.value) {
    return;
  }
  content.value = defaultContent.value;
  setUnsavedChanges();
}
</script>

<style lang="scss" scoped></style>
