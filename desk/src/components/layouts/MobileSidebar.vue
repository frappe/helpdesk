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
          <div><UserMenu class="p-2 mb-2" :options="profileSettings" /></div>
          <!-- notifications -->
          <div class="overflow-y-auto px-2" v-if="!isCustomerPortal">
            <div class="mb-3 flex flex-col gap-1">
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
              <SidebarLink
                v-if="!isCustomerPortal"
                class="relative"
                label="Dashboard"
                :icon="LucideLayoutDashboard"
                :to="'Dashboard'"
                :is-active="isActiveTab('Dashboard')"
                :is-expanded="true"
              />
            </div>
          </div>

          <div v-for="view in allViews" :key="view.label">
            <div
              v-if="!view.hideLabel && view.views?.length"
              class="mx-2 my-2 h-1"
            />
            <Section
              :label="view.label"
              :hideLabel="view.hideLabel"
              :opened="view.opened"
            >
              <template #header="{ opened, hide, toggle }">
                <div
                  v-if="!hide"
                  class="flex cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out"
                  :class="'ml-2 mt-4 h-7 w-auto opacity-100'"
                  @click="toggle()"
                >
                  <FeatherIcon
                    name="chevron-right"
                    class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                    :class="{ 'rotate-90': opened }"
                  />
                  <span>{{ view.label }}</span>
                </div>
              </template>
              <nav class="flex flex-col ml-2 mr-1">
                <SidebarLink
                  v-for="link in view.views"
                  :icon="link.icon"
                  :label="link.label"
                  :to="link.to"
                  :key="link.label"
                  :is-expanded="true"
                  :is-active="isActiveTab(link.to)"
                  class="my-0.5"
                  :onClick="link.onClick"
                />
              </nav>
            </Section>
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
import {
  Dialog,
  DialogOverlay,
  TransitionChild,
  TransitionRoot,
} from "@headlessui/vue";
import { computed, markRaw } from "vue";
import { useRoute, useRouter } from "vue-router";

import { Section } from "@/components";
import SidebarLink from "@/components/SidebarLink.vue";
import UserMenu from "@/components/UserMenu.vue";
import { useNotificationStore } from "@/stores/notification";

import { mobileSidebarOpened as sidebarOpened } from "@/composables/mobile";
import { currentView, useView } from "@/composables/useView";

import LucideBell from "~icons/lucide/bell";
import LucideLayoutDashboard from "~icons/lucide/layout-dashboard";

import { useAuthStore } from "@/stores/auth";
import { isCustomerPortal } from "@/utils";
import Apps from "../Apps.vue";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";
const { pinnedViews, publicViews } = useView();

const notificationStore = useNotificationStore();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const allViews = computed(() => {
  const items = isCustomerPortal.value
    ? customerPortalSidebarOptions
    : agentPortalSidebarOptions;

  const options = [
    {
      label: "All Views",
      hideLabel: true,
      opened: true,
      views: items,
    },
  ];
  if (publicViews.value?.length && !isCustomerPortal.value) {
    options.push({
      label: "Public Views",
      opened: true,
      hideLabel: false,
      views: parseViews(publicViews.value),
    });
  }
  if (pinnedViews.value?.length) {
    options.push({
      label: "Private Views",
      opened: true,
      hideLabel: false,
      views: parseViews(pinnedViews.value),
    });
  }
  return options;
});
function parseViews(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: view.icon,
      to: {
        name: view.route_name,
        query: { view: view.name },
      },
      onClick: () => {
        currentView.value = {
          label: view.label,
          icon: view.icon,
        };
      },
    };
  });
}

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
      const path = router.resolve({ name: "TicketsCustomer" });
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
  if (route.query.view) {
    return route.query.view == to?.query?.view;
  }
  return route.name === to;
}
</script>

<style scoped></style>
