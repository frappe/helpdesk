<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[{ label: 'Notifications', route: { name: 'Notifications' } }]"
      />
    </template>
    <template #right-header>
      <Tooltip :text="'Mark all as read'">
        <div>
          <Button
            :label="'Mark all as read'"
            @click="() => notificationStore.clear.submit()"
          >
            <template #prefix>
              <LucideCheckCheck class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </Tooltip>
    </template>
  </LayoutHeader>
  <div v-if="notificationStore.data.length" class="divide-y text-base">
    <RouterLink
      v-for="n in notificationStore.data"
      :key="n.name"
      class="flex cursor-pointer items-start gap-3.5 px-5 py-2.5 hover:bg-gray-100"
      :to="getRoute(n)"
      @click="
        () => {
          notificationStore.read(n.reference_ticket);
        }
      "
    >
      <UserAvatar :name="n.user_from" />
      <div>
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
      </div>
    </RouterLink>
  </div>
  <div v-else class="flex flex-1 flex-col items-center gap-2">
    <LucideBell class="h-20 w-20 text-gray-300" />
    <div class="text-lg font-medium text-gray-500">
      {{ "No new notifications" }}
    </div>
  </div>
</template>
<script setup lang="ts">
import { Breadcrumbs, Tooltip } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { useNotificationStore } from "@/stores/notification";
import { ref } from "vue";
import { onClickOutside } from "@vueuse/core";
import { dayjs } from "@/dayjs";
import { Notification } from "@/types";
import { UserAvatar } from "@/components";
import LucideBell from "~icons/lucide/bell";
const notificationStore = useNotificationStore();
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
