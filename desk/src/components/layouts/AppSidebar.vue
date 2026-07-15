<template>
  <Sidebar
    v-model:collapsed="collapsed"
    :disable-collapse="mobile"
    class="border-e border-outline-gray-1"
  >
    <div class="flex h-full flex-col p-2">
      <UserMenu :options="profileSettings" :is-collapsed="isCollapsed" />

      <div class="mt-2 flex-1 overflow-y-auto overflow-x-hidden">
        <template v-for="(section, index) in sections" :key="index">
          <SidebarLabel
            v-if="section.label"
            divider
            class="my-1 select-none"
            :class="section.collapsible && !isCollapsed && 'cursor-pointer'"
            @click="section.collapsible && toggleSection(section.label)"
          >
            <span class="flex items-center gap-1.5 text-sm font-medium">
              <span
                class="lucide-chevron-right size-4 shrink-0 text-ink-gray-9 transition-transform duration-300 ease-in-out"
                :class="{ 'rotate-90': isSectionOpen(section.label) }"
              />
              <span class="truncate">{{ section.label }}</span>
            </span>
          </SidebarLabel>
          <nav
            v-if="!section.label || isSectionOpen(section.label)"
            class="flex flex-col gap-0.5"
          >
            <SidebarItem
              v-for="item in section.items"
              :key="item.key"
              :label="__(item.label)"
              :active="item.isActive"
              :class="item.spacedTop && 'mt-4'"
              @click="item.onClick && item.onClick()"
            >
              <template #prefix>
                <span
                  class="relative grid size-4 shrink-0 place-items-center text-ink-gray-7"
                >
                  <component :is="item.icon" class="size-4" />
                  <span
                    v-if="item.key === 'notifications' && item.badge"
                    class="absolute -right-0.5 -top-0.5 size-1.5 rounded-full bg-surface-blue-5"
                  />
                </span>
              </template>
              <template #suffix>
                <span
                  v-if="item.shortcut"
                  class="me-2 flex items-center gap-0.5 font-medium text-ink-gray-5"
                >
                  <component :is="device.modifierIcon" class="h-3 w-3" />
                  <span class="text-sm">K</span>
                </span>
                <Badge
                  v-else-if="item.badge"
                  class="me-2"
                  :label="item.badge > 9 ? '9+' : item.badge"
                  theme="gray"
                  variant="subtle"
                />
                <Dropdown
                  v-else-if="item.view"
                  side="right"
                  align="start"
                  :options="viewActions(item.view, viewDialogConfig)"
                >
                  <template #default="{ open }">
                    <Button
                      variant="ghost"
                      icon="lucide-more-horizontal"
                      class="me-1 !size-6 rounded !text-ink-gray-7"
                      :class="
                        open
                          ? 'opacity-100'
                          : 'opacity-0 group-hover/sidebar-item:opacity-100'
                      "
                      @click.stop
                    />
                  </template>
                </Dropdown>
              </template>
            </SidebarItem>
          </nav>
        </template>
      </div>

      <div class="mt-auto flex flex-col gap-2">
        <slot name="footer" :is-collapsed="isCollapsed" />
        <SidebarCollapseToggle v-if="!mobile" />
      </div>
    </div>
  </Sidebar>
  <CP v-if="!mobile" v-model="showCommandPalette" />
  <ViewModal
    v-if="viewDialogConfig.show"
    v-model="viewDialogConfig"
    @update="(view, action) => handleView(view, action, viewDialogConfig)"
  />
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
import ViewModal from "@/components/ViewModal.vue";
import {
  Badge,
  Button,
  Dropdown,
  Sidebar,
  SidebarCollapseToggle,
  SidebarItem,
  SidebarLabel,
} from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, reactive, ref, watch } from "vue";
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
const { pinnedViews, publicViews, viewActions, handleView } = useView();

const showCommandPalette = ref(false);

// Local modal state for the per-view kebab menu (edit/duplicate). The action
// logic itself is shared via useView so the sidebar and breadcrumb stay in sync.
const viewDialogConfig = reactive({
  show: false,
  view: { label: "", icon: "", name: "" },
  mode: "create",
});

const collapsed = computed({
  get: () => !sidebarStore.isExpanded,
  set: (value) => sidebarStore.toggleExpanded(!value),
});

// The mobile drawer pins the sidebar open (disable-collapse), so it is never
// visually collapsed even when the store says so.
const isCollapsed = computed(() => collapsed.value && !props.mobile);

// Expanded/folded state of the collapsible view sections, keyed by label.
const closedSections = ref(new Set<string>());
const isSectionOpen = (label: string) => !closedSections.value.has(label);

function toggleSection(label: string) {
  if (isSectionOpen(label)) closedSections.value.add(label);
  else closedSections.value.delete(label);
}

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
    view,
  }));
}

watch(
  () => [route.name, route.query.view],
  () => (activeItem.value = currentRouteKey())
);
</script>
