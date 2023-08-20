<template>
  <div
    class="flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base -all duration-300 ease-in-out"
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
          v-for="option in extraOptions"
          v-bind="option"
          :key="option.label"
          :is-expanded="isExpanded"
          :is-active="option.to?.includes(route.name?.toString())"
        />
      </div>
    </span>
    <div class="grow" />
    <SidebarLink
      :icon="isExpanded ? 'lucide:chevrons-left' : 'lucide:chevrons-right'"
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
import SidebarLink from "@/components/SidebarLink.vue";
import { storeToRefs } from "pinia";

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
    icon: "lucide:ticket",
    to: AGENT_PORTAL_TICKET_LIST,
  },
  {
    label: "Dashboard",
    icon: "lucide:layout-grid",
    to: AGENT_PORTAL_DASHBOARD,
  },
  {
    label: "Agents",
    icon: "lucide:user",
    to: AGENT_PORTAL_AGENT_LIST,
  },
  {
    label: "Knowledge base",
    icon: "lucide:book-open",
    to: "DeskKBHome",
    isBeta: true,
  },
  {
    label: showExtra.value ? "Less" : "More",
    icon: "lucide:more-horizontal",
    onClick: () => (showExtra.value = !showExtra.value),
  },
]);

const extraOptions = [
  {
    label: "Support policies",
    icon: "lucide:scroll-text",
    to: AGENT_PORTAL_SLA_LIST,
  },
  {
    label: "Teams",
    icon: "lucide:users",
    to: AGENT_PORTAL_TEAM_LIST,
  },
  {
    label: "Escalation rules",
    icon: "lucide:arrow-up-from-line",
    to: AGENT_PORTAL_ESCALATION_RULE_LIST,
    isBeta: true,
  },
  {
    label: "Email accounts",
    icon: "lucide:at-sign",
    to: AGENT_PORTAL_EMAIL_LIST,
  },
  {
    label: "Ticket types",
    icon: "lucide:folder-open",
    to: AGENT_PORTAL_TICKET_TYPE_LIST,
  },
  {
    label: "Canned responses",
    icon: "lucide:cloud-lightning",
    to: AGENT_PORTAL_CANNED_RESPONSE_LIST,
    isBeta: true,
  },
  {
    label: "Customers",
    icon: "lucide:user-circle-2",
    to: AGENT_PORTAL_CUSTOMER_LIST,
  },
  {
    label: "Contacts",
    icon: "lucide:contact-2",
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
