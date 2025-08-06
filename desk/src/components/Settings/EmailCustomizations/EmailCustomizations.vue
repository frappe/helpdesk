<template>
  <div class="px-10 h-full overflow-y-auto flex flex-col isolate">
    <EmailCustomizationList
      v-if="selectedEmailType === null"
      :onEmailTypeSelect="onEmailTypeSelect"
    />
    <component
      v-else
      :is="emailTypeToComponent[selectedEmailType.name]"
      :onBack="resetSelectedEmailType"
      :emailType="selectedEmailType"
    ></component>
  </div>
</template>

<script setup lang="ts">
import { type Component, markRaw, ref } from "vue";
import type { EmailType, EmailTypeName } from "./types";
import EmailCustomizationList from "./EmailCustomizationList.vue";
import ShareFeedback from "./ShareFeedback.vue";

const selectedEmailType = ref<EmailType | null>(null);

const emailTypeToComponent: Record<
  EmailTypeName,
  Component<{ onBack: () => void; emailType: EmailType }>
> = {
  "share-feedback": markRaw(ShareFeedback),
};

function resetSelectedEmailType() {
  selectedEmailType.value = null;
}

function onEmailTypeSelect(emailType: EmailType) {
  selectedEmailType.value = emailType;
}
</script>

<style scoped></style>
