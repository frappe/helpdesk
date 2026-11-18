<template>
  <div class="flex flex-col h-full w-full">
    <div class="px-[4.4rem] pt-10 pb-6 relative z-10">
      <div
        class="flex flex-wrap lg:flex-nowrap items-start justify-between gap-x-4 gap-y-2"
      >
        <div class="flex min-w-0 flex-col gap-1 text-start">
          <slot name="title">
            <div v-if="backLabel" class="flex min-w-0 items-center gap-2">
              <SettingsBackButton :label="backLabel" @click="onBack" />
              <UnsavedBadge :show="Boolean(dirty)" />
            </div>
            <h1 v-else class="text-lg font-semibold text-ink-gray-8">
              {{ __(title) }}
            </h1>
          </slot>
          <slot
            name="description"
            v-if="Boolean($slots['description']) || Boolean(description)"
          >
            <p class="text-base text-ink-gray-6">
              {{ __(description) }}
            </p>
          </slot>
        </div>
        <slot name="header-actions" v-if="Boolean($slots['header-actions'])" />
      </div>
      <div class="mt-6" v-if="Boolean($slots['header-bottom'])">
        <slot name="header-bottom" />
      </div>
    </div>
    <div
      class="px-[4.4rem] pb-16 overflow-y-auto h-full flex flex-col text-start"
    >
      <slot name="content" />
    </div>
  </div>
</template>

<script setup lang="ts">
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import SettingsBackButton from "../../../../studio/helpdesk/components/settings/SettingsBackButton.vue";

defineProps<{
  title?: string;
  description?: string;
  backLabel?: string;
  onBack?: () => void;
  dirty?: boolean;
}>();
</script>
