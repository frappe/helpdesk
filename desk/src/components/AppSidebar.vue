<template>
  <div
    class="z-0 flex min-w-[256px] max-w-[256px] select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base duration-300 ease-in-out"
  >
    <Dropdown :options="dropdownOptions" class="mb-2">
      <template #default="{ open }">
        <button
          class="flex w-[15rem] items-center rounded-md p-2 text-left"
          :class="open ? 'bg-white shadow-sm' : 'hover:bg-gray-200'"
        >
          <img :src="HelpdeskLogo" class="h-8 w-8 rounded" />
          <div class="ml-2 flex flex-col">
            <div class="text-base font-medium leading-none text-gray-900">
              Helpdesk
            </div>
            <div
              class="mt-1 hidden text-sm leading-none text-gray-700 sm:inline"
            >
              {{ authStore.userName }}
            </div>
          </div>
          <FeatherIcon
            name="chevron-down"
            class="ml-auto h-5 w-5 text-gray-700"
          />
        </button>
      </template>
    </Dropdown>
    <SidebarLink
      label="Search"
      class="mb-1"
      :icon="LucideSearch"
      :on-click="() => openCommandPalette()"
    >
      <template #right>
        <span class="flex items-center gap-0.5 font-medium text-gray-600">
          <component :is="device.modifierIcon" class="h-3 w-3" />
          <span>K</span>
        </span>
      </template>
    </SidebarLink>
    <!-- <span class="mb-1"> -->
    <!--   <div -->
    <!--     v-if="notificationStore.unread" -->
    <!--     class="absolute z-20 h-1.5 w-1.5 translate-x-6 translate-y-1 rounded-full bg-gray-800" -->
    <!--     theme="gray" -->
    <!--     variant="solid" -->
    <!--   /> -->
    <!--   <SidebarLink -->
    <!--     class="relative" -->
    <!--     label="Notifications" -->
    <!--     :icon="LucideInbox" -->
    <!--     :on-click="() => notificationStore.toggle()" -->
    <!--     :is-expanded="isExpanded" -->
    <!--   > -->
    <!--     <template #right> -->
    <!--       <Badge -->
    <!--         v-if="isExpanded && notificationStore.unread" -->
    <!--         :label="notificationStore.unread" -->
    <!--         theme="gray" -->
    <!--         variant="subtle" -->
    <!--       /> -->
    <!--     </template> -->
    <!--   </SidebarLink> -->
    <!-- </span> -->
    <div class="space-y-1">
      <SidebarLink
        v-for="option in menuOptions"
        v-bind="option"
        :key="option.label"
        :is-active="option.to?.includes(route.name.toString())"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { Dropdown } from 'frappe-ui';
import { useAuthStore } from '@/stores/auth';
import { useKeymapStore } from '@/stores/keymap';
// import { useNotificationStore } from '@/stores/notification';
import { useSidebarStore } from '@/stores/sidebar';
import {
  AGENT_PORTAL_AGENT_LIST,
  AGENT_PORTAL_CANNED_RESPONSE_LIST,
  AGENT_PORTAL_CONTACT_LIST,
  AGENT_PORTAL_CUSTOMER_LIST,
  AGENT_PORTAL_DASHBOARD,
  AGENT_PORTAL_ESCALATION_RULE_LIST,
  AGENT_PORTAL_TEAM_LIST,
  AGENT_PORTAL_TICKET_LIST,
  AGENT_PORTAL_TICKET_TYPE_LIST,
  CUSTOMER_PORTAL_LANDING,
} from '@/router';
import { useDevice } from '@/composables';
import { SidebarLink } from '@/components';
// import UserMenu from './UserMenu.vue';
import HelpdeskLogo from '@/assets/logos/helpdesk.svg';
import LucideArrowLeftFromLine from '~icons/lucide/arrow-left-from-line';
import LucideArrowRightFromLine from '~icons/lucide/arrow-right-from-line';
import LucideArrowUpFromLine from '~icons/lucide/arrow-up-from-line';
import LucideBookOpen from '~icons/lucide/book-open';
import LucideCloudLightning from '~icons/lucide/cloud-lightning';
import LucideContact2 from '~icons/lucide/contact-2';
import LucideFolderOpen from '~icons/lucide/folder-open';
import LucideInbox from '~icons/lucide/inbox';
import LucideLayoutGrid from '~icons/lucide/layout-grid';
import LucideSearch from '~icons/lucide/search';
import LucideTicket from '~icons/lucide/ticket';
import LucideUser from '~icons/lucide/user';
import LucideUserCircle2 from '~icons/lucide/user-circle-2';
import LucideUsers from '~icons/lucide/users';

const route = useRoute();
const authStore = useAuthStore();
const keymapStore = useKeymapStore();
// const notificationStore = useNotificationStore();
const device = useDevice();

const menuOptions = computed(() =>
  [
    {
      label: 'Tickets',
      icon: LucideTicket,
      to: AGENT_PORTAL_TICKET_LIST,
    },
    {
      label: 'Dashboard',
      icon: LucideLayoutGrid,
      to: AGENT_PORTAL_DASHBOARD,
    },
    {
      label: 'Agents',
      icon: LucideUser,
      to: AGENT_PORTAL_AGENT_LIST,
      hide: !authStore.isAgent,
    },
    {
      label: 'Knowledge base',
      icon: LucideBookOpen,
      to: 'DeskKBHome',
      isBeta: true,
    },
    {
      label: 'Teams',
      icon: LucideUsers,
      to: AGENT_PORTAL_TEAM_LIST,
      hide: !authStore.isAgent,
    },
    {
      label: 'Escalation rules',
      icon: LucideArrowUpFromLine,
      to: AGENT_PORTAL_ESCALATION_RULE_LIST,
      isBeta: true,
      hide: !authStore.isAgent,
    },
    {
      label: 'Ticket types',
      icon: LucideFolderOpen,
      to: AGENT_PORTAL_TICKET_TYPE_LIST,
      hide: true,
    },
    {
      label: 'Canned responses',
      icon: LucideCloudLightning,
      to: AGENT_PORTAL_CANNED_RESPONSE_LIST,
      isBeta: true,
      hide: !authStore.isAgent,
    },
    {
      label: 'Customers',
      icon: LucideUserCircle2,
      to: AGENT_PORTAL_CUSTOMER_LIST,
      hide: !authStore.isAgent,
    },
    {
      label: 'Contacts',
      icon: LucideContact2,
      to: AGENT_PORTAL_CONTACT_LIST,
      hide: !authStore.isAgent,
    },
  ].filter((option) => !option.hide)
);

const dropdownOptions = [
  // {
  //   label: 'Shortcuts',
  //   icon: 'command',
  //   onClick: () => keymapStore.toggleVisibility(true),
  // },
  {
    label: 'Logout',
    icon: 'log-out',
    onClick: () => authStore.logout(),
  },
];

function openCommandPalette() {
  window.dispatchEvent(
    new KeyboardEvent('keydown', { key: 'k', metaKey: true })
  );
}
</script>
