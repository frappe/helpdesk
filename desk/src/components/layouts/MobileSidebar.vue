<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0 z-40">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="relative z-10 flex h-full w-[230px] flex-col border-r bg-gray-50 transition-all duration-300 ease-in-out"
        >
          <!-- user dropwdown -->
          <UserMenu class="p-2 mb-2" :options="profileSettings" />
          <!-- notifications -->
          <div class="overflow-y-auto px-2">
            <div class="mb-3 flex flex-col">
              <SidebarLink
                class="relative"
                label="Notifications"
                :icon="LucideBell"
                :on-click="() => (sidebarOpened = false)"
                :is-expanded="true"
                to="Notifications"
              >
                <template #right>
                  <Badge
                    v-if="notificationStore.unread"
                    :label="notificationStore.unread"
                    theme="gray"
                    variant="subtle"
                  />
                </template>
              </SidebarLink>
            </div>
          </div>

          <div class="mb-4 flex flex-col gap-1 px-2">
            <SidebarLink
              v-for="option in menuOptions"
              v-bind="option"
              :key="option.label"
              :is-expanded="true"
              :is-active="isActiveTab(option.to)"
              :on-click="() => (sidebarOpened = false)"
            />
          </div>
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-gray-600 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { computed, markRaw } from "vue";
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogOverlay,
} from "@headlessui/vue";
import { useRouter, useRoute } from "vue-router";

import UserMenu from "@/components/UserMenu.vue";
import SidebarLink from "@/components/SidebarLink.vue";
import { useNotificationStore } from "@/stores/notification";

import { mobileSidebarOpened as sidebarOpened } from "@/composables/mobile";
import LucideBell from "~icons/lucide/bell";

import { CUSTOMER_PORTAL_LANDING, CUSTOMER_PORTAL_ROUTES } from "@/router";
import Apps from "../Apps.vue";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";
import { useAuthStore } from "@/stores/auth";

const notificationStore = useNotificationStore();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const isCustomerPortal = computed(() =>
  CUSTOMER_PORTAL_ROUTES.includes(route.name)
);

const menuOptions = computed(() => {
  return isCustomerPortal.value
    ? customerPortalSidebarOptions
    : agentPortalSidebarOptions;
});

const customerPortalDropdown = computed(() => [
  {
    label: "Log out",
    icon: "log-out",
    onClick: () => authStore.logout(),
  },
]);

const agentPortalDropdown = computed(() => [
  {
    component: markRaw(Apps),
  },
  {
    label: "Customer portal",
    icon: "users",
    onClick: () => {
      const path = router.resolve({ name: CUSTOMER_PORTAL_LANDING });
      window.open(path.href);
    },
  },
  {
    icon: "life-buoy",
    label: "Support",
    onClick: () => window.open("https://t.me/frappedesk"),
  },
  {
    icon: "book-open",
    label: "Docs",
    onClick: () => window.open("https://docs.frappe.io/helpdesk"),
  },
  {
    label: "Log out",
    icon: "log-out",
    onClick: () => authStore.logout(),
  },
]);

const profileSettings = computed(() => {
  return isCustomerPortal.value
    ? customerPortalDropdown.value
    : agentPortalDropdown.value;
});

function isActiveTab(to: string) {
  return route.name === to;
}
</script>

<style scoped></style>
