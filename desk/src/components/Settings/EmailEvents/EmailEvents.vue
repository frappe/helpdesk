<template>
  <div class="px-10 h-full overflow-y-auto flex flex-col isolate">
    <EmailEventList
      v-if="selectedEmailEvent === null"
      :onEmailEventSelect="onEmailEventSelect"
    />
    <component
      v-else
      :is="emailEventToComponent[selectedEmailEvent.name]"
      :onBack="resetSelectedEmailEvent"
      :emailEvent="selectedEmailEvent"
    ></component>
  </div>
</template>

<script setup lang="ts">
import { type Component, markRaw, ref } from "vue";
import type { EmailEvent, EmailEventName } from "./types";
import EmailEventList from "./EmailEventList.vue";
import ShareFeedback from "./ShareFeedback.vue";
import Acknowledgement from "./Acknowledgement.vue";

const selectedEmailEvent = ref<EmailEvent | null>(null);

const emailEventToComponent: Record<
  EmailEventName,
  Component<{ onBack: () => void; emailEvent: EmailEvent }>
> = {
  "share-feedback": markRaw(ShareFeedback),
  acknowledgement: markRaw(Acknowledgement),
};

function resetSelectedEmailEvent() {
  selectedEmailEvent.value = null;
}

function onEmailEventSelect(event: EmailEvent) {
  selectedEmailEvent.value = event;
}
</script>

<style scoped></style>
