<template>
  <!-- Header -->
  <div class="pt-8 pb-2 bg-white sticky top-0 z-10">
    <SettingsLayoutHeader
      :title="__('Email Customizations')"
      :description="
        __('Personalize email settings and content to suit your needs')
      "
    />
  </div>
  <!-- Body -->
  <ul class="mt-4 pb-8 isolate">
    <li
      v-for="emailType in emailTypes"
      :key="emailType.name"
      class="flex items-center justify-between p-3 rounded relative"
    >
      <div class="flex flex-col">
        <h2
          class="text-p-base font-medium text-ink-gray-7 relative z-10 pointer-events-none"
        >
          {{ __(emailType.label) }}
        </h2>
        <p
          class="text-p-sm text-ink-gray-5 truncate relative z-10 pointer-events-none"
        >
          {{ __(emailType.description) }}
        </p>
      </div>
      <FeatherIcon
        name="chevron-right"
        class="text-ink-gray-7 size-4 relative z-10 pointer-events-none"
      />
      <button
        type="button"
        class="w-full h-full absolute top-0 left-0 hover:bg-surface-menu-bar rounded-[inherit]"
        @click="
          () => {
            props.onEmailTypeSelect(emailType);
          }
        "
      >
        <span class="sr-only">{{
          __args("customize {0}").format(emailType.name)
        }}</span>
      </button>
    </li>
  </ul>
</template>

<script setup lang="ts">
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import type { AtLeastOneEmailType, EmailType } from "./types";

const props = defineProps<{
  onEmailTypeSelect: (emailType: EmailType) => void;
}>();

const emailTypes: AtLeastOneEmailType = [
  {
    name: "share-feedback",
    label: "Share Feedback",
    description:
      "Configure the settings or personalize the content of the email",
  },
  // {
  //   name: "test-name",
  //   label: "Test Name",
  //   description: "Test description",
  // },
];
</script>

<style scoped></style>
