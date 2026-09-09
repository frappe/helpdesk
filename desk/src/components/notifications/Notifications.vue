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
      :title="__('Notifications')"
      @mark-as-read="handleNotificationClick"
      @mark-all-as-read="controller.markAllAsRead"
      @load-more="controller.loadMore"
      @close="notificationStore.toggle()"
    />
  </span>
</template>

<script setup lang="ts">
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { __ } from "@/translation";
import { NotificationLog, NotificationPanel } from "@framework/ui";
import { onClickOutside } from "@vueuse/core";
import { ref } from "vue";
import { useRouter } from "vue-router";

const notificationStore = useNotificationStore();
const controller = notificationStore.controller;
const sidebarStore = useSidebarStore();
const router = useRouter();
const target = ref(null);
onClickOutside(
  target,
  () => {
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
