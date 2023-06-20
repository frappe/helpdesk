<template>
  <div
    class="flex select-none flex-col border-r border-gray-200 bg-gray-50 px-3 py-2 text-base transition-all duration-300 ease-in-out"
    :class="{
      'w-56': sidebarStore.isExpanded,
      'w-13': !sidebarStore.isExpanded,
    }"
  >
    <UserMenu class="pb-2" :options="profileSettings" />
    <LinkGroup :options="menuOptions" />
    <span v-if="showExtra">
      <hr class="my-2" />
      <LinkGroup :options="extraOptions" />
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
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
import UserMenu from "./UserMenu.vue";
import LinkGroup from "./LinkGroup.vue";
import IconAgent from "~icons/lucide/user";
import IconAt from "~icons/lucide/at-sign";
import IconCannedResponse from "~icons/lucide/cloud-lightning";
import IconContact from "~icons/lucide/contact-2";
import IconCustomer from "~icons/lucide/user-circle-2";
import IconDashboard from "~icons/lucide/layout-grid";
import IconEscalation from "~icons/lucide/arrow-up-from-line";
import IconKnowledgeBase from "~icons/lucide/book-open";
import IconMore from "~icons/lucide/more-horizontal";
import IconSLA from "~icons/lucide/scroll-text";
import IconTeam from "~icons/lucide/users";
import IconTicket from "~icons/lucide/ticket";
import IconTicketType from "~icons/lucide/folder-open";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const keymapStore = useKeymapStore();
const sidebarStore = useSidebarStore();

const menuOptions = computed(() => [
  {
    label: "Tickets",
    icon: IconTicket,
    to: AGENT_PORTAL_TICKET_LIST,
  },
  {
    label: "Dashboard",
    icon: IconDashboard,
    to: AGENT_PORTAL_DASHBOARD,
  },
  {
    label: "Agents",
    icon: IconAgent,
    to: AGENT_PORTAL_AGENT_LIST,
  },
  {
    label: "Knowledge base",
    icon: IconKnowledgeBase,
    to: "DeskKBHome",
    isBeta: true,
  },
  {
    label: showExtra.value ? "Less" : "More",
    icon: IconMore,
    onClick: () => (showExtra.value = !showExtra.value),
  },
]);

const extraOptions = [
  {
    label: "Support policies",
    icon: IconSLA,
    to: AGENT_PORTAL_SLA_LIST,
  },
  {
    label: "Teams",
    icon: IconTeam,
    to: AGENT_PORTAL_TEAM_LIST,
  },
  {
    label: "Escalation rules",
    icon: IconEscalation,
    to: AGENT_PORTAL_ESCALATION_RULE_LIST,
    isBeta: true,
  },
  {
    label: "Email accounts",
    icon: IconAt,
    to: AGENT_PORTAL_EMAIL_LIST,
  },
  {
    label: "Ticket types",
    icon: IconTicketType,
    to: AGENT_PORTAL_TICKET_TYPE_LIST,
  },
  {
    label: "Canned responses",
    icon: IconCannedResponse,
    to: AGENT_PORTAL_CANNED_RESPONSE_LIST,
    isBeta: true,
  },
  {
    label: "Customers",
    icon: IconCustomer,
    to: AGENT_PORTAL_CUSTOMER_LIST,
  },
  {
    label: "Contacts",
    icon: IconContact,
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
