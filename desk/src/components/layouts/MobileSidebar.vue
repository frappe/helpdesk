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
        <div class="relative z-10 h-full w-fit">
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
import { useRoute } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import { CUSTOMER_PORTAL_ROOT } from "@/utils";
import { useColorScheme } from "frappe-ui";
import LucideMoon from "~icons/lucide/moon";
import LucideSun from "~icons/lucide/sun";

import { mobileSidebarOpened as sidebarOpened } from "@/composables/mobile";
import { useApps } from "@/composables/useApps";
import { __ } from "@/translation";
import AppSidebar from "./AppSidebar.vue";
import {
  expiryPresets,
  expirySummary,
  useAgentStatusStore,
} from "@/stores/agentStatus";

const { colorScheme, toggleColorScheme } = useColorScheme();
const { appsMenuOption } = useApps();
const route = useRoute();
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
const availabilityMenuOption = computed(() => {
  const expiresOn = agentStatusStore.myStatusExpiresOn;
  return {
    label: agentStatusStore.myStatus
      ? __(agentStatusStore.myStatus)
      : __("Set status"),
    // the clear time is visible without opening the menu
    ...(expiresOn && { description: expirySummary(expiresOn) }),
    icon: () => statusDot(agentStatusStore.myStatus),
    submenu: [
      {
        group: __("Status"),
        hideLabel: true,
        options: agentStatusStore.statusOptions.map((option) => ({
          label: __(option),
          icon: () => statusDot(option),
          selected: option === agentStatusStore.myStatus,
          onClick: () => agentStatusStore.setMyStatus(option),
        })),
      },
      ...(agentStatusStore.statusCanExpire(agentStatusStore.myStatus)
        ? [
            {
              group: __("Timer"),
              hideLabel: true,
              options: [expiryMenuOption()],
            },
          ]
        : []),
    ],
  };
});

// one row that opens the durations, so a phone never scrolls a long list
function expiryMenuOption() {
  const expiresOn = agentStatusStore.myStatusExpiresOn;
  return {
    label: expirySummary(expiresOn),
    icon: expiresOn ? "lucide-clock-fading" : "lucide-clock",
    submenu: [
      {
        group: __("Clear status after"),
        hideLabel: true,
        options: expiryPresets().map((preset) => ({
          label: preset.label,
          selected: agentStatusStore.isExpiryPresetActive(preset),
          onClick: () => agentStatusStore.applyExpiryPreset(preset),
        })),
      },
      {
        group: __("Clear"),
        hideLabel: true,
        options: [
          {
            label: __("Clear now"),
            onClick: () => agentStatusStore.clearMyStatus(),
          },
        ],
      },
    ],
  };
}

const themeMenuItem = computed(() => ({
  label: __("Toggle theme"),
  icon: colorScheme.value === "dark" ? LucideSun : LucideMoon,
  onClick: () => toggleColorScheme(),
}));

const profileSettings = computed(() => [
  appsMenuOption.value,
  ...(authStore.hasAgentRecord ? [availabilityMenuOption.value] : []),
  {
    label: __("Customer portal"),
    icon: "lucide-users",
    onClick: () => window.open(CUSTOMER_PORTAL_ROOT),
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

watch(
  () => route.fullPath,
  () => (sidebarOpened.value = false)
);
</script>
