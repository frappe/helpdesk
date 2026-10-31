<template>
  <TransitionRoot :show="sidebarOpened" @after-leave="onSidebarClosed">
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
          <AppSidebar mobile :profile-settings="profileSettings">
            <template #footer>
              <div class="px-2"><TrialCard /></div>
            </template>
          </AppSidebar>
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
  <AvailabilityDialog v-model:open="availabilityDialogOpen" />
</template>

<script setup lang="ts">
import {
  Dialog,
  DialogOverlay,
  TransitionChild,
  TransitionRoot,
} from "@headlessui/vue";
import { computed, h, ref, watch } from "vue";
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
import TrialCard from "./TrialCard.vue";
import { useAgentStatusStore } from "@/stores/agentStatus";
import AvailabilityDialog from "../AvailabilityDialog.vue";

const { colorScheme, toggleColorScheme } = useColorScheme();
const { appsMenuOption } = useApps();
const route = useRoute();
const authStore = useAuthStore();

const agentStatusStore = useAgentStatusStore();
const availabilityDialogOpen = ref(false);

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

const availabilityMenuOption = computed(() => ({
  label: agentStatusStore.myStatus
    ? __(agentStatusStore.myStatus)
    : __("Set status"),
  icon: () => statusDot(agentStatusStore.myStatus),
  onClick: () => {
    availabilityDialogPending = true;
    sidebarOpened.value = false;
  },
}));

// headless UI drops focus when the sidebar closes; give it back to the menu
// button, then open the dialog so it returns focus there too
let sidebarOpener: HTMLElement | null = null;
watch(sidebarOpened, (opened) => {
  if (opened) sidebarOpener = document.activeElement as HTMLElement | null;
});

let availabilityDialogPending = false;
function onSidebarClosed() {
  sidebarOpener?.focus();
  if (!availabilityDialogPending) return;
  availabilityDialogPending = false;
  availabilityDialogOpen.value = true;
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
