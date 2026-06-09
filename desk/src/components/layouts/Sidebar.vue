<template>
  <AppSidebar :profile-settings="profileSettings">
    <template #footer="{ isCollapsed }">
      <div class="px-2">
        <TrialBanner
          v-if="isFCSite && !isCustomerPortal"
          :isSidebarCollapsed="isCollapsed"
        />
        <GettingStartedBanner
          v-if="showOnboardingBanner"
          :isSidebarCollapsed="isCollapsed"
          appName="helpdesk"
        />
      </div>
      <SidebarItem
        v-if="isOnboardingStepsCompleted && !isCustomerPortal"
        :label="__('Help')"
        :icon="HelpIcon"
        :on-click="
          () => {
            showHelpModal = minimize ? true : !showHelpModal;
            minimize = !showHelpModal;
          }
        "
      />
    </template>
  </AppSidebar>

  <SettingsModal v-model="showSettingsModal" />
  <ShortcutsModal v-model="showShortcutsModal" />
  <HelpModal
    v-if="showHelpModal"
    v-model="showHelpModal"
    v-model:articles="articles"
    appName="helpdesk"
    title="Frappe Helpdesk"
    :logo="logo"
    docsLink="https://docs.frappe.io/helpdesk"
    :afterSkip="(step: string) => capture('onboarding_step_skipped_' + step)"
    :afterSkipAll="() => capture('onboarding_steps_skipped')"
    :afterReset="(step: string) => capture('onboarding_step_reset_' + step)"
    :afterResetAll="() => capture('onboarding_steps_reset')"
  />
  <IntermediateStepModal
    v-model="showIntermediateModal"
    :currentStep="currentStep"
  />
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";
import Apps from "@/components/Apps.vue";
import { FrappeCloudIcon, InviteCustomer } from "@/components/icons";
import ShortcutsModal from "@/components/modals/ShortcutsModal.vue";
import SettingsModal from "@/components/Settings/SettingsModal.vue";
import { confirmLoginToFrappeCloud } from "@/composables/fc";
import { useScreenSize } from "@/composables/screen";
import { showNewContactModal } from "@/pages/desk/contact/dialogState";
import {
  showAssignmentModal,
  showCommentBox,
  showEmailBox,
} from "@/pages/ticket/modalStates";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";
import { isCustomerPortal } from "@/utils";
import { call, SidebarItem, toast } from "frappe-ui";
import {
  GettingStartedBanner,
  HelpModal,
  IntermediateStepModal,
  minimize,
  showHelpModal,
  TrialBanner,
  useOnboarding,
} from "frappe-ui/frappe";

import { HelpIcon } from "frappe-ui/icons";
import { computed, h, markRaw, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AppSidebar from "./AppSidebar.vue";

import { useShortcut } from "@/composables/shortcuts";
import { __ } from "@/translation";
import FileText from "~icons/lucide/file-text";
import Globe from "~icons/lucide/globe";
import LucideKeyboard from "~icons/lucide/keyboard";
import LucideMail from "~icons/lucide/mail";
import MailOpen from "~icons/lucide/mail-open";
import MessageCircle from "~icons/lucide/message-circle";
import Ticket from "~icons/lucide/ticket";
import Timer from "~icons/lucide/timer";
import UserPen from "~icons/lucide/user-pen";
import LucideUserPlus from "~icons/lucide/user-plus";

import {
  setActiveSettingsTab,
  showSettingsModal,
} from "../Settings/settingsModal";

const { isMobileView } = useScreenSize();

const router = useRouter();
const authStore = useAuthStore();

const showShortcutsModal = ref(false);

const isFCSite = ref(window.is_fc_site);

const customerPortalDropdown = computed(() => [
  {
    group: __("Danger"),
    hideLabel: true,
    items: [
      {
        label: __("Log out"),
        icon: "lucide-log-out",
        onClick: () => authStore.logout(),
      },
    ],
  },
]);

const agentPortalDropdown = computed(() => [
  {
    component: markRaw(Apps),
  },
  {
    label: __("Customer portal"),
    icon: "lucide-users",
    onClick: () => {
      const path = router.resolve({ name: "TicketsCustomer" });
      window.open(path.href);
    },
  },
  {
    icon: "lucide-life-buoy",
    label: __("Support"),
    onClick: () => window.open("https://t.me/frappedesk"),
  },
  {
    icon: "lucide-book-open",
    label: __("Docs"),
    onClick: () => window.open("https://docs.frappe.io/helpdesk"),
  },
  {
    label: __("Login to Frappe Cloud"),
    icon: FrappeCloudIcon,
    onClick: () => confirmLoginToFrappeCloud(),
    condition: () => !isMobileView.value && window.is_fc_site,
  },
  {
    label: __("Shortcuts"),
    icon: h(LucideKeyboard),
    onClick: () => (showShortcutsModal.value = true),
  },
  {
    label: __("Settings"),
    icon: "lucide-settings",
    onClick: () => (showSettingsModal.value = true),
  },
  {
    group: __("Danger"),
    hideLabel: true,
    items: [
      {
        label: __("Log out"),
        icon: "lucide-log-out",
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
    title: __("Connect your support email"),
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
    title: __("Invite agents"),
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
    title: __("Setup SLA"),
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
    title: __("Create a ticket"),
    completed: false,
    icon: markRaw(Ticket),
    onClick: () => {
      router.push({ name: "TicketAgentNew" });
      minimize.value = true;
    },
  },
  {
    name: "assign_to_agent",
    title: __("Assign a ticket to an agent"),
    completed: false,
    dependsOn: "create_first_ticket",
    icon: markRaw(UserPen),
    onClick: async () => {
      await handleFirstTicketNavigation();
      showAssignmentModal.value = true;
      minimize.value = true;
    },
  },
  {
    name: "reply_on_ticket",
    title: __("Reply on a ticket"),
    completed: false,
    dependsOn: "create_first_ticket",
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
    title: __("Add a comment on a ticket"),
    completed: false,
    dependsOn: "create_first_ticket",
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
    title: __("Create an article"),
    completed: false,
    icon: markRaw(FileText),
    onClick: async () => {
      const generalCategory = await getGeneralCategory();
      router.push({
        name: "NewArticle",
        query: {
          title: __("General"),
        },
        params: { id: generalCategory },
      });
      minimize.value = true;
    },
  },
  {
    name: "add_invite_contact",
    title: __("Create & invite a contact"),
    completed: false,
    icon: markRaw(InviteCustomer),
    onClick: () => {
      minimize.value = true;
      currentStep.value = {
        title: __("Create & invite a contact"),
        buttonLabel: __("Create"),
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
    title: __("Explore customer portal"),
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
    title: __("Introduction"),
    opened: false,
    subArticles: [
      { name: "introduction", title: __("Introduction") },
      { name: "setting-up", title: __("Setting up") },
    ],
  },
  {
    title: __("Getting Started"),
    opened: false,
    subArticles: [
      {
        name: "lesson-1-your-first-ticket",
        title: __("Creating a ticket"),
      },
      {
        name: "lesson-2understanding-ticket-view",
        title: __("Understanding ticket view"),
      },
      {
        name: "lesson-3-agents-teams",
        title: __("Agents & Teams"),
      },
      {
        name: "customers-contacts",
        title: __("Customers & Contacts"),
      },
      {
        name: "lesson-4-knowledge-base",
        title: __("Knowledge Base"),
      },
      {
        name: "customer-portal",
        title: __("Customer Portal"),
      },
    ],
  },
  {
    title: __("Masters"),
    opened: false,
    subArticles: [
      { name: "ticket", title: __("Ticket") },
      { name: "agent", title: __("Agent") },
      { name: "team", title: __("Team") },
      { name: "contact", title: __("Contact") },
      { name: "customer", title: __("Customer") },
      { name: "knowledge-base", title: __("Knowledge Base") },
      { name: "saved-replies", title: __("Saved Replies") },
      { name: "service-level-agreement", title: __("Service Level Agreement") },
      { name: "ticket-type", title: __("Ticket Type") },
      { name: "ticket-priority", title: __("Ticket Priority") },
    ],
  },
  {
    title: __("Customizations"),
    opened: false,
    subArticles: [
      { name: "custom-actions", title: __("Custom Actions") },
      { name: "field-dependency", title: __("Field Dependency") },
      { name: "custom-views", title: __("Custom Views") },
      {
        name: "settings",
        title: __("Settings"),
      },
    ],
  },
  {
    title: __("Frappe Helpdesk Mobile"),
    opened: false,
    subArticles: [
      { name: "pwa-installation", title: __("Mobile App Installation") },
    ],
  },
]);

const showIntermediateModal = ref(false);
const currentStep = ref({});

const { isOnboardingStepsCompleted, setUp, updateOnboardingStep } =
  useOnboarding("helpdesk");

async function handleFirstTicketNavigation() {
  const ticket = await getFirstTicket();

  if (!ticket) {
    router.push({ name: "TicketAgentNew" });
    updateOnboardingStep("create_first_ticket", false); // reset the step as first ticket is not created
    toast.error(
      __("Please create a new ticket to proceed with the next step.")
    );
    return;
  }

  router.push({
    name: "TicketAgent",
    params: { ticketId: ticket },
  });
}

async function getFirstTicket() {
  let cachedTicket = localStorage.getItem("firstTicket");
  const ticket = await call("helpdesk.api.onboarding.get_first_ticket", {
    ticket: cachedTicket,
  });
  if (ticket) {
    localStorage.setItem("firstTicket", ticket);
  } else {
    localStorage.removeItem("firstTicket");
  }
  return ticket;
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
  useShortcut({ key: "h", meta: true }, () => {
    showHelpModal.value = !showHelpModal.value;
  });
}

onMounted(() => {
  setUpOnboarding();
  if (isCustomerPortal.value) return;
  useShortcut({ key: ",", meta: true }, () => {
    showSettingsModal.value = !showSettingsModal.value;
  });
});
</script>
