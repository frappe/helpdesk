<template>
  <div
    class="flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base duration-300 ease-in-out"
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
    <div class="overflow-y-auto">
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
    </div>
    <div class="grow" />
    <TrialBanner
      v-if="isFCSite && !isCustomerPortal"
      :isSidebarCollapsed="!isExpanded"
    />
    <GettingStartedBanner
      v-if="!isOnboardingStepsCompleted"
      :isSidebarCollapsed="!isExpanded"
      appName="helpdesk"
    />
    <SidebarLink
      v-if="isOnboardingStepsCompleted"
      :icon="LucideArrowLeftFromLine"
      label="Help"
      :isCollapsed="!isExpanded"
      @click="
        () => {
          showHelpModal = minimize ? true : !showHelpModal;
          minimize = !showHelpModal;
        }
      "
    >
      <template #icon>
        <HelpIcon class="h-4 w-4" />
      </template>
    </SidebarLink>
    <SidebarLink
      :icon="isExpanded ? LucideArrowLeftFromLine : LucideArrowRightFromLine"
      :is-active="false"
      :is-expanded="isExpanded"
      :label="isExpanded ? 'Collapse' : 'Expand'"
      :on-click="() => (isExpanded = !isExpanded)"
    />
    <SettingsModal
      v-model="showSettingsModal"
      :default-tab="defaultSettingsTab"
    />
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
import { FrappeCloudIcon } from "@/components/icons";
import SettingsModal from "@/components/Settings/SettingsModal.vue";
import UserMenu from "@/components/UserMenu.vue";
import { useDevice } from "@/composables";
import { confirmLoginToFrappeCloud } from "@/composables/fc";
import { useScreenSize } from "@/composables/screen";
import { currentView, useView } from "@/composables/useView";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
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
import { storeToRefs } from "pinia";
import { computed, h, markRaw, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  agentPortalSidebarOptions,
  customerPortalSidebarOptions,
} from "./layoutSettings";

import { InviteCustomer } from "@/components/icons";
import {
  showAssignmentModal,
  showCommentBox,
  showEmailBox,
} from "@/pages/ticket/modalStates";
import { reactive } from "vue";
import LucideArrowLeftFromLine from "~icons/lucide/arrow-left-from-line";
import LucideArrowRightFromLine from "~icons/lucide/arrow-right-from-line";
import LucideBell from "~icons/lucide/bell";
import FileText from "~icons/lucide/file-text";
import Globe from "~icons/lucide/globe";
import LucideMail from "~icons/lucide/mail";
import MailOpen from "~icons/lucide/mail-open";
import MessageCircle from "~icons/lucide/message-circle";
import LucideSearch from "~icons/lucide/search";
import Ticket from "~icons/lucide/ticket";
import Timer from "~icons/lucide/timer";
import UserPen from "~icons/lucide/user-pen";
import LucideUserPlus from "~icons/lucide/user-plus";
const { isMobileView } = useScreenSize();

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const { isExpanded, width } = storeToRefs(useSidebarStore());
const device = useDevice();
const showSettingsModal = ref(false);

const { pinnedViews, publicViews } = useView();
declare global {
  interface Window {
    is_fc_site: boolean;
  }
}
const isFCSite = ref(window.is_fc_site);

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

const logo = h(
  HDLogo,
  {
    class: "h-12 w-12",
  },
  null
);

const defaultSettingsTab = ref(0);
const onboardingStepsDesk = reactive({
  slaCreated: false,
});

const steps = computed(() => [
  {
    // done
    name: "setup_email_account",
    title: "Connect your support email",
    completed: false,
    icon: markRaw(LucideMail),
    onClick: () => {
      minimize.value = true;
      showSettingsModal.value = true;
      defaultSettingsTab.value = 0;
    },
  },
  {
    // done
    name: "invite_agents",
    title: "Invite agents",
    completed: false,
    icon: markRaw(LucideUserPlus),
    onClick: () => {
      minimize.value = true;
      router.push({ name: "AgentList", query: { invite: 1 } });
    },
  },
  {
    // left
    name: "setup_sla",
    title: "Set your first SLA",
    completed: onboardingStepsDesk.slaCreated,
    icon: markRaw(Timer),
    onClick: () => {
      console.log("clicked");
      const url = "/app/hd-service-level-agreement";
      window.open(url, "_blank");
    },
  },
  {
    // done
    // remaining is get created ticket and
    name: "create_first_ticket",
    title: "Create your first ticket",
    completed: false,
    icon: markRaw(Ticket),
    onClick: () => {
      router.push({ name: "TicketAgentNew" });
      minimize.value = true;
    },
  },
  {
    // done
    // remaining is get created ticket and
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
    // done
    // remaining is get created ticket and
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
    // done
    // remaining is get created ticket and
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
    // done
    name: "first_article",
    title: "Create your first article",
    completed: false,
    icon: markRaw(FileText),
    onClick: () => {
      console.log("clicked");
    },
  },
  {
    // left
    name: "add_invite_contact",
    title: "Add & invite a contact",
    completed: false,
    icon: markRaw(InviteCustomer),
    onClick: () => {
      console.log("clicked");
    },
  },
  {
    // left
    name: "explore_customer_portal",
    title: "Explore customer portal",
    completed: false,
    icon: markRaw(Globe),
    onClick: () => {
      console.log("clicked");
    },
  },
]);

const articles = ref([
  {
    title: "Introduction",
    opened: false,
    subArticles: [
      { name: "introduction", title: "Introduction" },
      { name: "setting-up", title: "Setting p" },
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

onMounted(() => {
  setUp(steps.value);
  // find completedSteps
  let storedSteps = JSON.parse(localStorage.getItem("onboardingStatus"));
  if (!storedSteps || storedSteps.helpdesk_onboarding_status == null) return;

  storedSteps = storedSteps.helpdesk_onboarding_status;
  let completedSteps = storedSteps
    .filter((step) => step.completed)
    .map((s) => s.name);
  console.log(completedSteps);
  if (completedSteps.includes("setup_sla")) {
    onboardingStepsDesk.slaCreated = true;
  }
  if (!completedSteps.includes("setup_sla")) {
    call("helpdesk.api.onboarding.get_first_sla").then((res: boolean) => {
      updateOnboardingStep("setup_sla", res);
    });
  }
});
</script>
