<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
<<<<<<< HEAD
        <div
          class="relative z-10 flex h-full w-[230px] flex-col border-r bg-surface-sidebar transition-all duration-300 ease-in-out"
        >
          <!-- user dropwdown -->
          <div class="p-1">
            <UserMenu :options="profileSettings" />
          </div>
          <div class="overflow-y-auto overflow-x-hidden">
            <!-- notifications -->
            <div v-if="!isCustomerPortal">
              <div class="flex flex-col gap-1">
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

            <div v-for="view in allViews" :key="view.label">
              <div v-if="!view.hideLabel && view.views?.length" />
              <div class="mx-2 my-1.5"></div>

              <Section
                :label="view.label"
                :hideLabel="view.hideLabel"
                :opened="view.opened"
              >
                <template #header="{ opened, hide, toggle }">
                  <div
                    v-if="!hide"
                    class="flex cursor-pointer gap-1.5 px-2 text-base-medium text-ink-gray-5 mx-2 transition-all duration-300 ease-in-out"
                    :class="'py-[7px] h-7.5 w-auto opacity-100'"
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
                <nav class="flex flex-col">
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
=======
        <div class="relative z-10 h-full">
          <AppSidebar mobile :profile-settings="profileSettings" />
>>>>>>> 8fa03b64 (fix(views): use icons instead of emojis)
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
        <DialogOverlay class="fixed inset-0 bg-black-overlay-500" />
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
import { computed, markRaw, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import { isCustomerPortal } from "@/utils";
import { useTheme } from "frappe-ui";
import LucideMoon from "~icons/lucide/moon";
import LucideSun from "~icons/lucide/sun";

import { mobileSidebarOpened as sidebarOpened } from "@/composables/mobile";
import { useApps } from "@/composables/useApps";
import { __ } from "@/translation";
import AppSidebar from "./AppSidebar.vue";
import AvailabilityMenuMobile from "../AvailabilityMenuMobile.vue";

const { currentTheme, toggleTheme } = useTheme();
const { appsMenuOption } = useApps();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const themeMenuItem = computed(() => ({
  label: __("Toggle theme"),
  icon: currentTheme.value === "dark" ? LucideSun : LucideMoon,
  onClick: () => toggleTheme(),
}));

const customerPortalDropdown = computed(() => [
  themeMenuItem.value,
  {
    label: __("Log out"),
    icon: "lucide-log-out",
    onClick: () => authStore.logout(),
  },
]);

const agentPortalDropdown = computed(() => [
  appsMenuOption.value,
  ...(authStore.hasAgentRecord
    ? [
        {
          component: markRaw(AvailabilityMenuMobile),
        },
      ]
    : []),
  {
    label: __("Customer portal"),
    icon: "lucide-users",
    onClick: () => {
      const path = router.resolve({ name: "TicketsCustomer" });
      window.open(path.href);
    },
  },
  {
    icon: "lucide-life-buoy",
    label: __("Support"),
    onClick: () => window.open("https://t.me/frappedesk"),
  },
  {
    icon: "lucide-book-open",
    label: __("Docs"),
    onClick: () => window.open("https://docs.frappe.io/helpdesk"),
  },
  themeMenuItem.value,
  {
    label: __("Log out"),
    icon: "lucide-log-out",
    onClick: () => authStore.logout(),
  },
]);

const profileSettings = computed(() => {
  return isCustomerPortal.value
    ? customerPortalDropdown.value
    : agentPortalDropdown.value;
});

watch(
  () => route.fullPath,
  () => (sidebarOpened.value = false)
);
</script>
