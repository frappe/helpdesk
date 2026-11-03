<template>
  <span
    v-if="notificationStore.visible"
    ref="target"
    class="fixed z-10 h-screen overflow-auto bg-surface-base notifications-panel"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      'inset-inline-start': sidebarStore.width,
    }"
  >
    <NotificationPanel
      v-bind="controller"
      @mark-as-read="handleNotificationClick"
      @mark-all-as-read="controller.markAllAsRead"
      @load-more="controller.loadMore"
      @close="notificationStore.toggle()"
    >
      <template #header="{ markAllAsRead, close }">
        <div class="flex items-center gap-2 px-4 py-2 pt-4">
          <span class="text-md font-medium mr-auto">
            {{ __("Notifications") }}
          </span>
          <Button
            variant="ghost"
            size="sm"
            :tooltip="__('Mark all as read')"
            :aria-label="__('Mark all as read')"
            :icon="LucideCheckCheck"
            @click="markAllAsRead"
          />
          <Button
            variant="ghost"
            size="sm"
            :tooltip="__('Close')"
            :aria-label="__('Close')"
            :icon="LucideX"
            @click="close"
          />
        </div>
        <NotificationFilters />
      </template>
    </NotificationPanel>
  </span>
</template>

<script setup lang="ts">
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { __ } from "@/translation";
import { NotificationLog, NotificationPanel } from "@framework/ui";
import { onClickOutside, useEventListener } from "@vueuse/core";
import { Button } from "frappe-ui";
import { ref } from "vue";
import { useRouter } from "vue-router";
import LucideCheckCheck from "~icons/lucide/check-check";
import LucideX from "~icons/lucide/x";
import NotificationFilters from "./NotificationFilters.vue";

const notificationStore = useNotificationStore();
const controller = notificationStore.controller;
const sidebarStore = useSidebarStore();
const router = useRouter();
const target = ref(null);

// An open menu makes the page inert, so its dismiss click lands outside the
// panel; the menu is gone by click time, so note it on pointerdown.
let menuWasOpen = false;
useEventListener(
  window,
  "pointerdown",
  () => (menuWasOpen = !!document.querySelector("[role='menu']")),
  { capture: true }
);

onClickOutside(
  target,
  () => {
    if (menuWasOpen) return;
    if (notificationStore.visible) {
      notificationStore.toggle();
    }
  },
  {
    ignore: ["#notifications-btn"],
  }
);

function handleNotificationClick(n: NotificationLog) {
  controller.markAsRead(n.name);
  const route = notificationStore.routeFor(n);
  notificationStore.toggle();
  if (route) router.push(route);
}
</script>
<style lang="css">
[dir="rtl"] .notifications-panel {
  box-shadow: -8px 0px 8px rgba(0, 0, 0, 0.1) !important;
}
</style>
