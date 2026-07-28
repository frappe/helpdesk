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
import { computed, h, watch } from "vue";
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
import { useAgentStatusStore } from "@/stores/agentStatus";

const { currentTheme, toggleTheme } = useTheme();
const { appsMenuOption } = useApps();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const agentStatusStore = useAgentStatusStore();

// The menu injects `size-4` onto icon components; keep that as the outer
// footprint (so it lines up with the lucide icons) and center the actual
// 2.5 dot inside it, same as the availability indicator elsewhere.
const statusDot = (status: string) =>
  h("span", { class: "flex items-center justify-center" }, [
    h("span", {
      class: [
        "size-2.5 shrink-0 rounded-full",
        agentStatusStore.statusColor(status),
      ],
    }),
  ]);

// Native Dropdown submenu (same pattern as appsMenuOption) instead of a nested
// Popover: reka-ui keeps the submenu inside the viewport on narrow screens,
// where a right-placed popover overlapped the menu items below it.
const availabilityMenuOption = computed(() => ({
  label: agentStatusStore.myStatus
    ? __(agentStatusStore.myStatus)
    : __("Set status"),
  icon: () => statusDot(agentStatusStore.myStatus),
  submenu: agentStatusStore.statusOptions.map((option) => ({
    label: __(option),
    icon: () => statusDot(option),
    onClick: () => agentStatusStore.setMyStatus(option),
  })),
}));

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
  ...(authStore.hasAgentRecord ? [availabilityMenuOption.value] : []),
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
