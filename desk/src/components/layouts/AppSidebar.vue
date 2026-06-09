<template>
  <Sidebar
    v-model:collapsed="collapsed"
    :disable-collapse="mobile"
    :sections="sections"
  >
    <template #header="{ isCollapsed }">
      <UserMenu :options="profileSettings" :is-collapsed="isCollapsed" />
    </template>

    <template
      #section-header="{
        label,
        collapsible,
        isSidebarCollapsed,
        isOpen,
        toggle,
      }"
    >
      <template v-if="label">
        <div
          v-if="isSidebarCollapsed"
          class="flex items-center justify-center px-2 py-1.5"
        >
          <hr class="w-full border-t border-ink-gray-3" />
        </div>
        <div
          v-else
          class="flex cursor-pointer items-center gap-1.5 px-2 pb-2.5 pt-[11px] text-sm font-medium text-ink-gray-5"
          @click="collapsible && toggle()"
        >
          <span
            class="lucide-chevron-right size-4 shrink-0 text-ink-gray-9 transition-transform duration-300 ease-in-out"
            :class="{ 'rotate-90': isOpen }"
          />
          <span class="truncate">{{ label }}</span>
        </div>
      </template>
    </template>

    <template #sidebar-item="{ item, isCollapsed }">
      <button
        type="button"
        :title="isCollapsed ? __(item.label) : undefined"
        class="flex h-7.5 w-full items-center rounded px-2 text-ink-gray-8"
        :class="[
          item.isActive
            ? 'bg-surface-selected shadow-sm'
            : 'hover:bg-surface-gray-2',
          { 'mt-4': item.spacedTop },
        ]"
        @click="item.onClick && item.onClick()"
      >
        <span
          class="relative grid size-4 shrink-0 place-items-center text-ink-gray-7"
        >
          <component :is="item.icon" class="size-4" />
          <span
            v-if="item.key === 'notifications' && item.badge"
            class="absolute -right-0.5 -top-0.5 size-1.5 rounded-full bg-blue-400"
          />
        </span>
        <span
          class="ms-2 flex min-w-0 flex-1 items-center justify-between text-sm transition-all duration-300 ease-in-out"
          :class="
            isCollapsed ? 'w-0 overflow-hidden opacity-0' : 'w-auto opacity-100'
          "
        >
          <span class="truncate text-start">{{ __(item.label) }}</span>
          <span
            v-if="item.shortcut"
            class="flex items-center gap-0.5 font-medium text-ink-gray-5"
          >
            <component :is="device.modifierIcon" class="h-3 w-3" />
            <span>K</span>
          </span>
          <Badge
            v-else-if="item.badge"
            :label="item.badge > 9 ? '9+' : item.badge"
            theme="gray"
            variant="subtle"
          />
        </span>
      </button>
    </template>

    <template #footer-items="slotProps">
      <slot name="footer" v-bind="slotProps" />
    </template>
  </Sidebar>
  <CP v-if="!mobile" v-model="showCommandPalette" />
</template>

<script setup lang="ts">
import CP from "@/components/command-palette/CP.vue";
import UserMenu from "@/components/UserMenu.vue";
import { useDevice } from "@/composables";
import { currentView, useView } from "@/composables/useView";
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { useTelephonyStore } from "@/stores/telephony";
import { __ } from "@/translation";
import { getIcon, isCustomerPortal } from "@/utils";
import { Badge, Sidebar } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, ref, watch } from "vue";
import type { RouteLocationRaw } from "vue-router";
import { useRoute, useRouter } from "vue-router";
import LucideBell from "~icons/lucide/bell";
import LucideSearch from "~icons/lucide/search";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";

const props = defineProps<{
  profileSettings: any[];
  mobile?: boolean;
}>();

const route = useRoute();
const router = useRouter();
const device = useDevice();
const notificationStore = useNotificationStore();
const sidebarStore = useSidebarStore();
const { isCallingEnabled } = storeToRefs(useTelephonyStore());
const { pinnedViews, publicViews } = useView();

const showCommandPalette = ref(false);

const collapsed = computed({
  get: () => !sidebarStore.isExpanded,
  set: (value) => sidebarStore.toggleExpanded(!value),
});

// Optimistic active item: set immediately on click so the highlight is
// instant, then kept in sync with the route (browser back/forward, external
// navigation). A view's key is its name; a nav item's key is its route name.
const activeItem = ref<string | null>(currentRouteKey());

function currentRouteKey(): string | null {
  return (route.query.view as string) || (route.name as string) || null;
}

function selectItem(key: string, to: RouteLocationRaw, onSelect?: () => void) {
  activeItem.value = key;
  onSelect?.();
  router.push(to);
}

const navItems = computed(() => {
  const options = isCustomerPortal.value
    ? customerPortalSidebarOptions
    : agentPortalSidebarOptions;
  return options
    .filter((item) => isCallingEnabled.value || item.label !== __("Call Logs"))
    .map((option, index) => ({
      label: option.label,
      icon: option.icon,
      isActive: activeItem.value === option.to,
      onClick: () => selectItem(option.to, { name: option.to }),
      // Separate the nav group from the search/notification tools above it.
      spacedTop: index === 0 && !isCustomerPortal.value,
      key: option.label,
    }));
});

const searchItem = computed(() => ({
  label: __("Search"),
  icon: LucideSearch,
  onClick: () => (showCommandPalette.value = true),
  shortcut: true,
  key: "search",
}));

const notificationItem = computed(() =>
  props.mobile
    ? {
        label: __("Notifications"),
        icon: LucideBell,
        isActive: activeItem.value === "Notifications",
        onClick: () => selectItem("Notifications", { name: "Notifications" }),
        badge: notificationStore.unread,
        key: "notifications",
      }
    : {
        label: __("Notifications"),
        icon: LucideBell,
        onClick: () => notificationStore.toggle(),
        badge: notificationStore.unread,
        key: "notifications",
      }
);

const mainItems = computed(() => {
  if (isCustomerPortal.value) return navItems.value;
  const top = props.mobile
    ? [notificationItem.value]
    : [searchItem.value, notificationItem.value];
  return [...top, ...navItems.value];
});

const sections = computed(() => {
  const result = [{ label: "", items: mainItems.value, collapsible: false }];
  if (publicViews.value?.length && !isCustomerPortal.value) {
    result.push({
      label: __("Public Views"),
      items: parseViews(publicViews.value),
      collapsible: true,
    });
  }
  if (pinnedViews.value?.length) {
    result.push({
      label: __("Private Views"),
      items: parseViews(pinnedViews.value),
      collapsible: true,
    });
  }
  return result;
});

function parseViews(views: any[]) {
  return views.map((view) => ({
    label: view.label,
    icon: getIcon(view.icon),
    isActive: activeItem.value === view.name,
    onClick: () =>
      selectItem(
        view.name,
        { name: view.route_name, query: { view: view.name } },
        () => {
          currentView.value = { label: view.label, icon: view.icon };
        }
      ),
    key: view.name,
  }));
}

watch(
  () => [route.name, route.query.view],
  () => (activeItem.value = currentRouteKey())
);
</script>
