<template>
  <div
    v-if="visible"
    class="mx-4 mb-2 flex items-start gap-2 rounded-lg bg-surface-gray-2 px-3 py-2.5"
  >
    <LucideBellRing class="my-0.5 size-4 shrink-0 text-ink-gray-7" />
    <div class="flex flex-1 flex-col items-start gap-2">
      <p class="text-p-sm text-ink-gray-7">
        {{ __("Get a desktop notification whenever a new ticket comes in.") }}
      </p>
      <Button
        size="sm"
        variant="solid"
        :label="__('Turn on')"
        @click="desktopNotificationStore.enable"
      />
    </div>
    <Button
      variant="ghost"
      size="sm"
      :tooltip="__('Dismiss')"
      :aria-label="__('Dismiss')"
      :icon="LucideX"
      @click="dismissed = true"
    />
  </div>
</template>

<script setup lang="ts">
import { useDesktopNotificationStore } from "@/stores/desktopNotification";
import { __ } from "@/translation";
import { useLocalStorage } from "@vueuse/core";
import { Button } from "frappe-ui";
import { computed } from "vue";
import LucideBellRing from "~icons/lucide/bell-ring";
import LucideX from "~icons/lucide/x";

const desktopNotificationStore = useDesktopNotificationStore();
const dismissed = useLocalStorage(
  "helpdesk-desktop-notification-banner",
  false
);

// once the browser has an answer, granted or blocked, there is nothing to ask
const visible = computed(
  () =>
    desktopNotificationStore.isSupported &&
    desktopNotificationStore.permission === "default" &&
    !dismissed.value
);
</script>
