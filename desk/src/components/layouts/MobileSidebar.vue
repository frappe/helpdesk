<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full rtl:translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full rtl:translate-x-full"
      >
        <div class="relative z-10 h-full">
          <AppSidebar mobile :profile-settings="profileSettings" />
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
import AppSidebar from "./AppSidebar.vue";
import Apps from "../Apps.vue";
import AvailabilityMenuMobile from "../AvailabilityMenuMobile.vue";

const { currentTheme, toggleTheme } = useTheme();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const themeMenuItem = computed(() => ({
  label: "Toggle theme",
  icon: currentTheme.value === "dark" ? LucideSun : LucideMoon,
  onClick: () => toggleTheme(),
}));

const customerPortalDropdown = computed(() => [
  themeMenuItem.value,
  {
    label: "Log out",
    icon: "lucide-log-out",
    onClick: () => authStore.logout(),
  },
]);

const agentPortalDropdown = computed(() => [
  {
    component: markRaw(Apps),
  },
  ...(authStore.hasAgentRecord
    ? [
        {
          component: markRaw(AvailabilityMenuMobile),
        },
      ]
    : []),
  {
    label: "Customer portal",
    icon: "lucide-users",
    onClick: () => {
      const path = router.resolve({ name: "TicketsCustomer" });
      window.open(path.href);
    },
  },
  {
    icon: "lucide-life-buoy",
    label: "Support",
    onClick: () => window.open("https://t.me/frappedesk"),
  },
  {
    icon: "lucide-book-open",
    label: "Docs",
    onClick: () => window.open("https://docs.frappe.io/helpdesk"),
  },
  themeMenuItem.value,
  {
    label: "Log out",
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
