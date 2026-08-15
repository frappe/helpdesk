<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          { label: __('Notifications'), route: { name: 'Notifications' } },
        ]"
      />
    </template>
    <template #right-header>
      <Tooltip :text="__('Mark all as read')">
        <div>
          <Button
            :label="__('Mark all as read')"
            @click="() => controller.markAllAsRead()"
          >
            <template #prefix>
              <LucideCheckCheck class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </Tooltip>
    </template>
  </LayoutHeader>
  <NotificationPanel
    v-bind="controller"
    @mark-as-read="handleNotificationClick"
    @mark-all-as-read="controller.markAllAsRead"
    @load-more="controller.loadMore"
  >
    <template #header><span /></template>
    <template #empty>
      <div class="flex flex-1 flex-col items-center gap-2 py-12">
        <LucideBell class="h-20 w-20 text-ink-gray-2" />
        <div class="text-lg-medium text-ink-gray-4">
          {{ __("No new notifications") }}
        </div>
      </div>
    </template>
  </NotificationPanel>
</template>
<script setup lang="ts">
import LayoutHeader from "@/components/LayoutHeader.vue";
import { useNotificationStore } from "@/stores/notification";
import { __ } from "@/translation";
import { NotificationLog, NotificationPanel } from "@framework/ui";
import { Breadcrumbs, Tooltip } from "frappe-ui";
import { useRouter } from "vue-router";
import LucideBell from "~icons/lucide/bell";

const notificationStore = useNotificationStore();
const controller = notificationStore.controller;
const router = useRouter();

function handleNotificationClick(n: NotificationLog) {
  controller.markAsRead(n.name);
  const route = notificationStore.routeFor(n);
  if (route) router.push(route);
}
</script>
