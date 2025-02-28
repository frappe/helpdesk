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
            :label="
              notificationStore.unread > 9 ? '9+' : notificationStore.unread
            "
            theme="gray"
            variant="subtle"
          />
        </template>
      </SidebarLink>
    </div>
    <div v-for="view in allViews" :key="view.label">
      <div
        v-if="!view.hideLabel && !isExpanded && view.views?.length"
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
            :class="
              !isExpanded
                ? 'ml-0 h-0 overflow-hidden opacity-0'
                : 'mt-4 h-7 w-auto opacity-100'
            "
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
            :is-expanded="isExpanded"
            :is-active="isActiveTab(link.to)"
            class="my-0.5 emoji"
            :onClick="link.onClick"
          />
        </nav>
      </Section>
    </div>
    <div class="grow" />
    <SidebarLink
      :icon="isExpanded ? LucideArrowLeftFromLine : LucideArrowRightFromLine"
      :is-active="false"
      :is-expanded="isExpanded"
      :label="isExpanded ? 'Collapse' : 'Expand'"
      :on-click="() => (isExpanded = !isExpanded)"
    />
    <SettingsModal v-model="showSettingsModal" />
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { useDevice } from "@/composables";
import { SidebarLink } from "@/components";
import UserMenu from "@/components/UserMenu.vue";
import LucideArrowLeftFromLine from "~icons/lucide/arrow-left-from-line";
import LucideArrowRightFromLine from "~icons/lucide/arrow-right-from-line";
import LucideBell from "~icons/lucide/bell";
import LucideSearch from "~icons/lucide/search";
import SettingsModal from "@/components/Settings/SettingsModal.vue";
import Apps from "@/components/Apps.vue";
import { isCustomerPortal } from "@/utils";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";
import { Section } from "@/components";
import { useView, currentView } from "@/composables/useView";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const { isExpanded, width } = storeToRefs(useSidebarStore());
const device = useDevice();
const showSettingsModal = ref(false);

const { pinnedViews, publicViews } = useView();

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
    condition: () => authStore.isAdmin || authStore.isManager,
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

function isActiveTab(to: any) {
  if (route.query.view) {
    return route.query.view == to?.query?.view;
  }
  return route.name === to;
}

function openCommandPalette() {
  window.dispatchEvent(
    new KeyboardEvent("keydown", { key: "k", metaKey: true })
  );
}
</script>
