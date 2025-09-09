<template>
  <div
    class="flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base duration-300 ease-in-out"
    :style="{
      'min-width': width,
      'max-width': width,
    }"
  >
    <UserMenu class="mb-2" :options="profileSettings" />
    <SidebarLink
      v-if="!isCustomerPortal"
      label="Search"
      class="my-0.5"
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
    <SidebarLink
      v-if="!isCustomerPortal"
      class="relative my-0.5 min-h-7"
      label="Dashboard"
      :icon="LucideLayoutDashboard"
      :to="'Dashboard'"
      :is-active="isActiveTab('Dashboard')"
      :is-expanded="isExpanded"
    />
    <div class="mb-4" v-if="!isCustomerPortal">
      <div
        v-if="notificationStore.unread"
        class="absolute size-1.5 translate-x-6 translate-y-1 rounded-full bg-blue-400 left-1"
        theme="gray"
        variant="solid"
      />
      <SidebarLink
        class="relative my-0.5"
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
    <div class="overflow-y-auto overflow-x-hidden">
      <div v-for="view in allViews" :key="view.label">
        <div
          v-if="!view.hideLabel && !isExpanded && view.views?.length"
          class="mx-2 my-2 h-1 border-b"
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
    </div>
    <div class="grow" />
    <div class="flex flex-col gap-2">
      <TrialBanner
        v-if="isFCSite && !isCustomerPortal"
        :isSidebarCollapsed="!isExpanded"
      />
      <GettingStartedBanner
        v-if="showOnboardingBanner"
        :isSidebarCollapsed="!isExpanded"
        appName="helpdesk"
      />
      <SidebarLink
        v-if="isOnboardingStepsCompleted && !isCustomerPortal"
        :icon="HelpIcon"
        :label="'Help'"
        :is-expanded="isExpanded"
        @click="
          () => {
            showHelpModal = minimize ? true : !showHelpModal;
            minimize = !showHelpModal;
          }
        "
      />

      <SidebarLink
        :icon="isExpanded ? LucideArrowLeftFromLine : LucideArrowRightFromLine"
        :is-active="false"
        :is-expanded="isExpanded"
        :label="isExpanded ? 'Collapse' : 'Expand'"
        :on-click="() => (isExpanded = !isExpanded)"
      />
    </div>
    <TrialBanner
      v-if="isFCSite && !isCustomerPortal"
      :isSidebarCollapsed="!isExpanded"
    />
    <SettingsModal v-model="showSettingsModal" />
    <HelpModal
      v-if="showHelpModal"
      v-model="showHelpModal"
      v-model:articles="articles"
      appName="helpdesk"
      title="Frappe Helpdesk"
      :logo="logo"
      docsLink="https://docs.frappe.io/helpdesk"
      :afterSkip="(step) => capture('onboarding_step_skipped_' + step)"
      :afterSkipAll="() => capture('onboarding_steps_skipped')"
      :afterReset="(step) => capture('onboarding_step_reset_' + step)"
      :afterResetAll="() => capture('onboarding_steps_reset')"
    />
    <IntermediateStepModal
      v-model="showIntermediateModal"
      :currentStep="currentStep"
    />
  </div>
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import { Section, SidebarLink } from "@/components";
import Apps from "@/components/Apps.vue";
import { FrappeCloudIcon, InviteCustomer } from "@/components/icons";
import SettingsModal from "@/components/Settings/SettingsModal.vue";
import UserMenu from "@/components/UserMenu.vue";
import { useDevice } from "@/composables";
import { confirmLoginToFrappeCloud } from "@/composables/fc";
import { useScreenSize } from "@/composables/screen";
import { currentView, useView } from "@/composables/useView";
import { showNewContactModal } from "@/pages/desk/contact/dialogState";
import {
  showAssignmentModal,
  showCommentBox,
  showEmailBox,
} from "@/pages/ticket/modalStates";
import { useAuthStore } from "@/stores/auth";
import { useNotificationStore } from "@/stores/notification";
import { useSidebarStore } from "@/stores/sidebar";
import { capture } from "@/telemetry";
import { isCustomerPortal } from "@/utils";
import { call } from "frappe-ui";
import {
  GettingStartedBanner,
  HelpModal,
  IntermediateStepModal,
  minimize,
  showHelpModal,
  TrialBanner,
  useOnboarding,
} from "frappe-ui/frappe";

import HelpIcon from "frappe-ui/frappe/Icons/HelpIcon.vue";
import { storeToRefs } from "pinia";
import { computed, h, markRaw, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";

import { globalStore } from "@/stores/globalStore";
import LucideArrowLeftFromLine from "~icons/lucide/arrow-left-from-line";
import LucideArrowRightFromLine from "~icons/lucide/arrow-right-from-line";
import LucideBell from "~icons/lucide/bell";
import FileText from "~icons/lucide/file-text";
import Globe from "~icons/lucide/globe";
import LucideLayoutDashboard from "~icons/lucide/layout-dashboard";
import LucideMail from "~icons/lucide/mail";
import MailOpen from "~icons/lucide/mail-open";
import MessageCircle from "~icons/lucide/message-circle";
import LucideSearch from "~icons/lucide/search";
import Ticket from "~icons/lucide/ticket";
import Timer from "~icons/lucide/timer";
import UserPen from "~icons/lucide/user-pen";
import LucideUserPlus from "~icons/lucide/user-plus";
import { useTelephonyStore } from "@/stores/telephony";
import { setActiveSettingsTab } from "../Settings/settingsModal";

const { isMobileView } = useScreenSize();

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const { isExpanded, width } = storeToRefs(useSidebarStore());
const device = useDevice();
const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const showSettingsModal = ref(false);

const { pinnedViews, publicViews } = useView();

const isFCSite = ref(window.is_fc_site);

const allViews = computed(() => {
  let items = isCustomerPortal.value
    ? customerPortalSidebarOptions
    : agentPortalSidebarOptions;

  if (!isCallingEnabled.value) {
    items = items.filter((item) => item.label !== "Call Logs");
  }

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
      const path = router.resolve({ name: "TicketsCustomer" });
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
    label: "Login to Frappe Cloud",
    icon: FrappeCloudIcon,
    onClick: () => confirmLoginToFrappeCloud(),
    condition: () => !isMobileView.value && window.is_fc_site,
  },
  {
    label: "Settings",
    icon: "settings",
    onClick: () => (showSettingsModal.value = true),
    condition: () => authStore.isAdmin || authStore.isManager,
  },
  {
    group: "Danger",
    hideLabel: true,
    items: [
      {
        label: "Log out",
        icon: "log-out",
        onClick: () => authStore.logout(),
      },
    ],
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

const logo = h(
  HDLogo,
  {
    class: "h-12 w-12",
  },
  null
);

const showOnboardingBanner = computed(() => {
  return (
    !isCustomerPortal.value &&
    !isOnboardingStepsCompleted.value &&
    authStore.isManager
  );
});

const steps = [
  {
    name: "setup_email_account",
    title: "Connect your support email",
    completed: false,
    icon: markRaw(LucideMail),
    onClick: () => {
      minimize.value = true;
      showSettingsModal.value = true;
      setActiveSettingsTab("Email Accounts");
    },
  },
  {
    name: "invite_agents",
    title: "Invite agents",
    completed: false,
    icon: markRaw(LucideUserPlus),
    onClick: () => {
      minimize.value = true;
      showSettingsModal.value = true;
      setActiveSettingsTab("Invite Agents");
    },
  },
  {
    name: "setup_sla",
    title: "Setup SLA",
    completed: false,
    icon: markRaw(Timer),
    onClick: () => {
      setActiveSettingsTab("SLA Policies");
      showSettingsModal.value = true;
      minimize.value = true;
    },
  },
  {
    name: "create_first_ticket",
    title: "Create a ticket",
    completed: false,
    icon: markRaw(Ticket),
    onClick: () => {
      router.push({ name: "TicketAgentNew" });
      minimize.value = true;
    },
  },
  {
    name: "assign_to_agent",
    title: "Assign a ticket to an agent",
    completed: false,
    icon: markRaw(UserPen),
    onClick: async () => {
      await handleFirstTicketNavigation();
      showAssignmentModal.value = true;
      minimize.value = true;
    },
  },
  {
    name: "reply_on_ticket",
    title: "Reply on a ticket",
    completed: false,
    icon: markRaw(MailOpen),
    onClick: async () => {
      await handleFirstTicketNavigation();
      showEmailBox.value = true;
      showCommentBox.value = false;
      minimize.value = true;
    },
  },
  {
    name: "comment_on_ticket",
    title: "Add a comment on a ticket",
    completed: false,
    icon: markRaw(MessageCircle),
    onClick: async () => {
      await handleFirstTicketNavigation();
      showCommentBox.value = true;
      showEmailBox.value = false;
      minimize.value = true;
    },
  },
  {
    name: "first_article",
    title: "Create an article",
    completed: false,
    icon: markRaw(FileText),
    onClick: async () => {
      const generalCategory = await getGeneralCategory();
      router.push({
        name: "NewArticle",
        query: {
          title: "General",
        },
        params: { id: generalCategory },
      });
      minimize.value = true;
    },
  },
  {
    name: "add_invite_contact",
    title: "Create & invite a contact",
    completed: false,
    icon: markRaw(InviteCustomer),
    onClick: () => {
      minimize.value = true;
      currentStep.value = {
        title: "Create & invite a contact",
        buttonLabel: "Create",
        videoURL: "/assets/helpdesk/desk/videos/createInviteContact.mp4",
        onClick: async () => {
          showIntermediateModal.value = false;
          router.push({ name: "ContactList" });
          showNewContactModal.value = true;
        },
      };
      showIntermediateModal.value = true;
    },
  },
  {
    name: "explore_customer_portal",
    title: "Explore customer portal",
    completed: false,
    icon: markRaw(Globe),
    onClick: () => {
      window.open("/helpdesk/my-tickets", "_blank");
      updateOnboardingStep("explore_customer_portal");
      minimize.value = true;
    },
  },
];

const articles = ref([
  {
    title: "Introduction",
    opened: false,
    subArticles: [
      { name: "introduction", title: "Introduction" },
      { name: "setting-up", title: "Setting up" },
    ],
  },
  {
    title: "Getting Started",
    opened: false,
    subArticles: [
      {
        name: "lesson-1-your-first-ticket",
        title: "Creating a ticket",
      },
      {
        name: "lesson-2understanding-ticket-view",
        title: "Understanding ticket view",
      },
      {
        name: "lesson-3-agents-teams",
        title: "Agents & Teams",
      },
      {
        name: "customers-contacts",
        title: "Customers & Contacts",
      },
      {
        name: "lesson-4-knowledge-base",
        title: "Knowledge Base",
      },
      {
        name: "customer-portal",
        title: "Customer Portal",
      },
    ],
  },
  {
    title: "Masters",
    opened: false,
    subArticles: [
      { name: "ticket", title: "Ticket" },
      { name: "agent", title: "Agent" },
      { name: "team", title: "Team" },
      { name: "contact", title: "Contact" },
      { name: "customer", title: "Customer" },
      { name: "knowledge-base", title: "Knowledge Base" },
      { name: "canned-response", title: "Canned Responses" },
      { name: "service-level-agreement", title: "Service Level Agreement" },
      { name: "ticket-type", title: "Ticket Type" },
      { name: "ticket-priority", title: "Ticket Priority" },
    ],
  },
  {
    title: "Customizations",
    opened: false,
    subArticles: [
      { name: "custom-actions", title: "Custom Actions" },
      { name: "field-dependency", title: "Field Dependency" },
      { name: "custom-views", title: "Custom Views" },
      {
        name: "settings",
        title: "Settings",
      },
    ],
  },
  {
    title: "Frappe Helpdesk Mobile",
    opened: false,
    subArticles: [
      { name: "pwa-installation", title: "Mobile App Installation" },
    ],
  },
]);

const showIntermediateModal = ref(false);
const currentStep = ref({});

const { isOnboardingStepsCompleted, setUp, updateOnboardingStep } =
  useOnboarding("helpdesk");

async function handleFirstTicketNavigation() {
  const ticket = await getFirstTicket();

  if (ticket) {
    router.push({
      name: "TicketAgent",
      params: { ticketId: ticket },
    });
  } else {
    router.push({ name: "TicketAgentNew" });
  }
}

async function getFirstTicket() {
  let ticket = localStorage.getItem("firstTicket");
  if (ticket) return ticket;
  return await call("helpdesk.api.onboarding.get_first_ticket");
}

async function getGeneralCategory() {
  let generalCategory = localStorage.getItem("generalCategoryId");
  if (!generalCategory) {
    generalCategory = await call(
      "helpdesk.api.onboarding.get_general_category_id"
    );
    if (!generalCategory) return;
    localStorage.setItem("generalCategoryId", generalCategory);
  }
  return generalCategory;
}

function setUpOnboarding() {
  if (!authStore.isManager) return;
  setUp(steps);
}

onMounted(() => {
  setUpOnboarding();
});
</script>
