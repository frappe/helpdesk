<template>
  <span
    v-if="notificationStore.visible"
    ref="target"
    class="fixed z-10 h-screen overflow-auto bg-white"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      left: sidebarStore.width,
    }"
  >
    <div
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-5 py-2.5"
    >
      <span class="text-lg font-medium">Notifications</span>
      <div>
        <Button
          theme="blue"
          variant="ghost"
          @click="() => notificationStore.clear.submit()"
          v-if="notificationStore.data.length"
        >
          <template #icon>
            <LucideCheckCheck class="h-4 w-4" />
          </template>
        </Button>
        <Button
          theme="gray"
          variant="ghost"
          @click="() => notificationStore.toggle()"
        >
          <template #icon>
            <LucideX class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </div>
    <div class="divide-y text-base" v-if="notificationStore.data.length">
      <RouterLink
        v-for="n in notificationStore.data"
        :key="n.name"
        class="flex cursor-pointer items-start gap-3.5 px-5 py-2.5 hover:bg-gray-100"
        :to="getRoute(n)"
        @click="
          () => {
            handleNotificationClick(n);
          }
        "
      >
        <UserAvatar :name="n.user_from" />
        <span>
          <div class="mb-2 leading-5">
            <span class="space-x-1 text-gray-700">
              <span class="font-medium text-gray-900">{{ n.user_from }}</span>
              <span v-if="n.notification_type === 'Mention'"
                >mentioned you in ticket</span
              >
              <span v-if="n.notification_type === 'Assignment'"
                >assigned you a ticket</span
              >
              <span v-if="n.notification_type === 'Reaction'"
                >has reopened the ticket</span
              >
              <span class="font-medium text-gray-900">{{
                n.reference_ticket
              }}</span>
            </span>
          </div>
          <div class="flex items-center gap-2">
            <div class="text-sm text-gray-600">
              {{ dayjs.tz(n.creation).fromNow() }}
            </div>
            <div v-if="!n.read" class="h-1.5 w-1.5 rounded-full bg-blue-400" />
          </div>
        </span>
      </RouterLink>
    </div>
    <div
      class="p-5 text-center text-gray-500 flex flex-col items-center justify-center gap-2 mt-20"
      v-else
    >
      <LucideBell class="size-6" />
      <p class="text-base text-ink-gray-8">You are all caught up!</p>
    </div>
  </span>
</template>

<script setup lang="ts">
import { UserAvatar } from "@/components";
import { dayjs } from "@/dayjs";
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { Notification } from "@/types";
import { onClickOutside } from "@vueuse/core";
import { ref } from "vue";

const notificationStore = useNotificationStore();
const sidebarStore = useSidebarStore();
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

function handleNotificationClick(n: Notification) {
  notificationStore.toggle();
  if (n.read) return;
  notificationStore.read(n.reference_ticket);
}

function getRoute(n: Notification) {
  switch (n.notification_type) {
    case "Mention":
      return {
        name: "TicketAgent",
        params: {
          ticketId: n.reference_ticket,
        },
        hash: "#" + n.reference_comment,
      };
    case "Assignment":
    case "Reaction":
      return {
        name: "TicketAgent",
        params: {
          ticketId: n.reference_ticket,
        },
      };
  }
}
</script>
