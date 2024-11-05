<template>
  <div
    class="z-0 flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base duration-300 ease-in-out"
    :style="{
      'min-width': width,
      'max-width': width,
    }"
  >
    <UserMenu class="mb-2 ml-0.5" :options="profileSettings" />
    <SidebarLink
      v-if="!isCustomerPortal"
      label="Search"
      class="mb-1"
      :icon="LucideSearch"
      :on-click="() => openCommandPalette()"
      :is-expanded="isExpanded"
    >
      <template #right>
        <span class="flex items-center gap-0.5 font-medium text-gray-600">
          <component :is="device.modifierIcon" class="h-3 w-3" />
          <span>K</span>
        </span>
      </template>
    </SidebarLink>
    <div class="mb-4" v-if="!isCustomerPortal">
      <div
        v-if="notificationStore.unread"
        class="absolute z-20 h-1.5 w-1.5 translate-x-6 translate-y-1 rounded-full bg-blue-400 left-1"
        theme="gray"
        variant="solid"
      />
      <SidebarLink
        class="relative"
        label="Notifications"
        :icon="LucideBell"
        :on-click="() => notificationStore.toggle()"
        :is-expanded="isExpanded"
      >
        <template #right>
          <Badge
            v-if="isExpanded && notificationStore.unread"
            :label="notificationStore.unread"
            theme="gray"
            variant="subtle"
          />
        </template>
      </SidebarLink>
    </div>
    <div class="mb-4 flex flex-col gap-1">
      <SidebarLink
        v-for="option in menuOptions"
        v-bind="option"
        :key="option.label"
        :is-expanded="isExpanded"
        :is-active="isActiveTab(option.to)"
      />
    </div>
    <div class="grow" />
    <SidebarLink
      :icon="isExpanded ? LucideArrowLeftFromLine : LucideArrowRightFromLine"
      :is-active="false"
      :is-expanded="isExpanded"
      :label="isExpanded ? 'Collapse' : 'Expand'"
      :on-click="() => (isExpanded = !isExpanded)"
    />
    <SettingsModal v-if="authStore.isAdmin" v-model="showSettingsModal" />
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { CUSTOMER_PORTAL_LANDING, CUSTOMER_PORTAL_ROUTES } from "@/router";
import { useDevice } from "@/composables";
import { SidebarLink } from "@/components";
import UserMenu from "@/components/UserMenu.vue";
import LucideArrowLeftFromLine from "~icons/lucide/arrow-left-from-line";
import LucideArrowRightFromLine from "~icons/lucide/arrow-right-from-line";
import LucideBell from "~icons/lucide/bell";
import LucideSearch from "~icons/lucide/search";
import SettingsModal from "@/components/Settings/SettingsModal.vue";
import Apps from "@/components/Apps.vue";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const { isExpanded, width } = storeToRefs(useSidebarStore());
const device = useDevice();
const showSettingsModal = ref(false);
const isCustomerPortal = route.meta.public ?? false;

const menuOptions = computed(() => {
  return isCustomerPortal
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
    label: "Settings",
    icon: "settings",
    onClick: () => (showSettingsModal.value = true),
  },
  {
    label: "Log out",
    icon: "log-out",
    onClick: () => authStore.logout(),
  },
]);

const profileSettings = computed(() => {
  return isCustomerPortal
    ? customerPortalDropdown.value
    : agentPortalDropdown.value;
});

function isActiveTab(to: string) {
  return route.name === to;
}

function openCommandPalette() {
  window.dispatchEvent(
    new KeyboardEvent("keydown", { key: "k", metaKey: true })
  );
}
</script>
