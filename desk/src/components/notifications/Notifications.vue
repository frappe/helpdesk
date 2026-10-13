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
        <div class="flex items-center justify-between gap-2 px-4 py-2">
          <TabButtons
            v-model="notificationStore.readFilter"
            :options="readOptions"
          />
          <Dropdown :options="categoryOptions" align="end">
            <Button :label="categoryLabel">
              <template #prefix>
                <LucideList class="h-4 w-4" />
              </template>
              <template #suffix>
                <LucideChevronDown class="h-4 w-4" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </template>
    </NotificationPanel>
  </span>
</template>

<script setup lang="ts">
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { __ } from "@/translation";
import { NotificationLog, NotificationPanel } from "@framework/ui";
import { onClickOutside } from "@vueuse/core";
import { Button, Dropdown, TabButtons } from "frappe-ui";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import LucideCheckCheck from "~icons/lucide/check-check";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideList from "~icons/lucide/list";
import LucideX from "~icons/lucide/x";

const notificationStore = useNotificationStore();
const controller = notificationStore.controller;
const sidebarStore = useSidebarStore();
const router = useRouter();
const target = ref(null);

const readOptions = [
  { label: __("All"), value: "all" },
  { label: __("Unread"), value: "unread" },
];

// Notification Log types helpdesk produces; core writes Mention and Assignment
const categories = [
  { label: __("All categories"), value: "" },
  { label: __("Mentions"), value: "Mention" },
  { label: __("Assignments"), value: "Assignment" },
  { label: __("Reactions"), value: "Reaction" },
  { label: __("Reopened tickets"), value: "Ticket Reopened" },
];
const categoryOptions = categories.map((c) => ({
  label: c.label,
  onClick: () => (notificationStore.category = c.value),
}));
const categoryLabel = computed(
  () => categories.find((c) => c.value === notificationStore.category)?.label
);

onClickOutside(
  target,
  () => {
    if (notificationStore.visible) {
      notificationStore.toggle();
    }
  },
  {
    // the category menu renders in a portal outside the panel
    ignore: ["#notifications-btn", "[role='menu']"],
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
