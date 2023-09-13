<template>
  <div
    class="-all flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base duration-300 ease-in-out"
    :style="isExpanded ? widthExpanded : widthMinimised"
  >
    <UserMenu class="mb-2 ml-0.5" :options="profileSettings" />
    <div class="flex flex-col gap-1">
      <SidebarLink
        v-for="option in menuOptions"
        v-bind="option"
        :key="option.label"
        :is-expanded="isExpanded"
        :is-active="option.to?.includes(route.name.toString())"
      />
    </div>
    <span v-if="showExtra">
      <hr class="my-2" />
      <div class="flex flex-col gap-1">
        <SidebarLink
          v-for="option in extraOptions.filter((o) => !o.hide)"
          v-bind="option"
          :key="option.label"
          :is-expanded="isExpanded"
          :is-active="option.to?.includes(route.name?.toString())"
        />
      </div>
    </span>
    <div class="grow" />
    <SidebarLink
      :icon="isExpanded ? LucideChevronsLeft : LucideChevronsRight"
      :is-active="false"
      :is-expanded="isExpanded"
      :label="isExpanded ? 'Collapse' : 'Expand'"
      :on-click="() => (isExpanded = !isExpanded)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { useKeymapStore } from "@/stores/keymap";
import { useSidebarStore } from "@/stores/sidebar";
import {
  AGENT_PORTAL_AGENT_LIST,
  AGENT_PORTAL_CANNED_RESPONSE_LIST,
  AGENT_PORTAL_CONTACT_LIST,
  AGENT_PORTAL_CUSTOMER_LIST,
  AGENT_PORTAL_DASHBOARD,
  AGENT_PORTAL_EMAIL_LIST,
  AGENT_PORTAL_ESCALATION_RULE_LIST,
  AGENT_PORTAL_SLA_LIST,
  AGENT_PORTAL_TEAM_LIST,
  AGENT_PORTAL_TICKET_LIST,
  AGENT_PORTAL_TICKET_TYPE_LIST,
  CUSTOMER_PORTAL_LANDING,
} from "@/router";
import { SidebarLink } from "@/components";
import UserMenu from "./UserMenu.vue";
import LucideArrowUpFromLine from "~icons/lucide/arrow-up-from-line";
import LucideAtSign from "~icons/lucide/at-sign";
import LucideBookOpen from "~icons/lucide/book-open";
import LucideChevronsLeft from "~icons/lucide/chevrons-left";
import LucideChevronsRight from "~icons/lucide/chevrons-right";
import LucideCloudLightning from "~icons/lucide/cloud-lightning";
import LucideContact2 from "~icons/lucide/contact-2";
import LucideFolderOpen from "~icons/lucide/folder-open";
import LucideLayoutGrid from "~icons/lucide/layout-grid";
import LucideMoreHorizontal from "~icons/lucide/more-horizontal";
import LucideScrollText from "~icons/lucide/scroll-text";
import LucideTicket from "~icons/lucide/ticket";
import LucideUser from "~icons/lucide/user";
import LucideUserCircle2 from "~icons/lucide/user-circle-2";
import LucideUsers from "~icons/lucide/users";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const keymapStore = useKeymapStore();
const { isExpanded } = storeToRefs(useSidebarStore());

const widthExpanded = {
  "min-width": "256px",
  "max-width": "256px",
};
const widthMinimised = {
  "min-width": "50px",
  "max-width": "50px",
};
const menuOptions = computed(() => [
  {
    label: "Tickets",
    icon: LucideTicket,
    to: AGENT_PORTAL_TICKET_LIST,
  },
  {
    label: "Dashboard",
    icon: LucideLayoutGrid,
    to: AGENT_PORTAL_DASHBOARD,
  },
  {
    label: "Agents",
    icon: LucideUser,
    to: AGENT_PORTAL_AGENT_LIST,
  },
  {
    label: "Knowledge base",
    icon: LucideBookOpen,
    to: "DeskKBHome",
    isBeta: true,
  },
  {
    label: showExtra.value ? "Less" : "More",
    icon: LucideMoreHorizontal,
    onClick: () => (showExtra.value = !showExtra.value),
  },
]);

const extraOptions = [
  {
    label: "Support policies",
    icon: LucideScrollText,
    to: AGENT_PORTAL_SLA_LIST,
    hide: true,
  },
  {
    label: "Teams",
    icon: LucideUsers,
    to: AGENT_PORTAL_TEAM_LIST,
  },
  {
    label: "Escalation rules",
    icon: LucideArrowUpFromLine,
    to: AGENT_PORTAL_ESCALATION_RULE_LIST,
    isBeta: true,
  },
  {
    label: "Email accounts",
    icon: LucideAtSign,
    to: AGENT_PORTAL_EMAIL_LIST,
    hide: true,
  },
  {
    label: "Ticket types",
    icon: LucideFolderOpen,
    to: AGENT_PORTAL_TICKET_TYPE_LIST,
    hide: true,
  },
  {
    label: "Canned responses",
    icon: LucideCloudLightning,
    to: AGENT_PORTAL_CANNED_RESPONSE_LIST,
    isBeta: true,
  },
  {
    label: "Customers",
    icon: LucideUserCircle2,
    to: AGENT_PORTAL_CUSTOMER_LIST,
  },
  {
    label: "Contacts",
    icon: LucideContact2,
    to: AGENT_PORTAL_CONTACT_LIST,
  },
];

const profileSettings = [
  {
    label: "Shortcuts",
    icon: "command",
    onClick: () => keymapStore.toggleVisibility(true),
  },
  {
    label: "Customer portal",
    icon: "users",
    onClick: () => {
      const path = router.resolve({ name: CUSTOMER_PORTAL_LANDING });
      window.open(path.href, "_blank");
    },
  },
  {
    label: "Log out",
    icon: "log-out",
    onClick: () => authStore.logout(),
  },
];

const showExtra = ref(!!extraOptions.find((o) => o.to === route.name));
</script>
