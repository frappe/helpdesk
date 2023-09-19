<template>
  <TransitionRoot
    as="div"
    class="fixed z-40 h-screen overflow-auto bg-white"
    :show="notificationStore.visible"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '300px',
      'min-width': '300px',
      left: sidebarStore.width,
    }"
    enter="transition duration-200 ease-in-out transform"
    enter-from="-translate-x-full"
    enter-to="translate-x-0"
    leave="transition duration-200 ease-in-out transform"
    leave-from="translate-x-0"
    leave-to="-translate-x-full"
  >
    <span>
      <div
        class="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-5 py-2.5"
      >
        <span class="text-lg font-medium">Notifications</span>
        <span>
          <Button theme="blue" variant="ghost">
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
        </span>
      </div>
      <div class="grow divide-y px-4 py-3 text-base">
        <div
          v-for="n in 10"
          :key="n"
          class="flex items-start gap-3.5 px-2 py-2.5"
        >
          <UserAvatar user="hello@ssiyad.com" />
          <span>
            <div class="mb-2 leading-5">
              Nathan updated status of Ticket 00095 - Delivery status
              notification to ”Replied”
            </div>
            <div class="text-sm text-gray-600">1h ago</div>
          </span>
          <span
            class="h-1.5 w-1.5 shrink-0 self-center rounded-full bg-blue-500"
          />
        </div>
      </div>
    </span>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { TransitionRoot } from "@headlessui/vue";
import { useSidebarStore } from "@/stores/sidebar";
import { useNotificationStore } from "@/stores/notification";
import { UserAvatar } from "@/components";

const notificationStore = useNotificationStore();
const sidebarStore = useSidebarStore();
</script>
