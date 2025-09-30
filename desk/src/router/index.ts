import { useScreenSize } from "@/composables/screen";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { isCustomerPortal } from "@/utils";
import { createRouter, createWebHistory } from "vue-router";
const { isMobileView } = useScreenSize();

export const LOGIN_PAGE = "/login?redirect-to=/helpdesk";

// type the meta fields
declare module "vue-router" {
  interface RouteMeta {
    auth?: boolean;
    agent?: boolean;
    admin?: boolean;
    public?: boolean;
    onSuccessRoute?: string;
    parent?: string;
  }
}

const routes = [
  // Agent Portal Routes
  {
    path: "/",
    name: "Home",
    redirect: "/tickets",
  },

  {
    path: "/tickets",
    name: "TicketsAgent",
    component: () => import("@/pages/ticket/Tickets.vue"),
  },
  {
    path: "/tickets/:ticketId",
    name: "TicketAgent",
    component: () =>
      import(`@/pages/ticket/${handleMobileView("TicketAgent")}.vue`),
    props: true,
  },
  {
    path: "/tickets/new/:templateId?",
    name: "TicketAgentNew",
    component: () => import("@/pages/ticket/TicketNew.vue"),
    props: true,
    meta: {
      onSuccessRoute: "TicketAgent",
      parent: "TicketsAgent",
    },
  },
  {
    path: "/notifications",
    name: "Notifications",
    component: () => import("@/pages/MobileNotifications.vue"),
  },
  {
    path: "/kb",
    name: "AgentKnowledgeBase",
    component: () => import("@/pages/knowledge-base/KnowledgeBaseAgent.vue"),
  },
  {
    path: "/kb/articles/:articleId",
    name: "Article",
    component: () => import("@/pages/knowledge-base/Article.vue"),
    props: true,
  },
  {
    path: "/articles/new/:id",
    name: "NewArticle",
    component: () => import("@/pages/knowledge-base/NewArticle.vue"),
    props: true,
  },
  {
    path: "/customers",
    name: "CustomerList",
    component: () => import("@/pages/desk/customer/Customers.vue"),
  },
  {
    path: "/contacts",
    name: "ContactList",
    component: () => import("@/pages/desk/contact/Contacts.vue"),
  },
  {
    path: "/agents",
    name: "AgentList",
    redirect: "/tickets",
  },
  {
    path: "/teams",
    name: "Teams",
    redirect: "/tickets",
  },
  {
    path: "/teams/:teamId",
    name: "Team",
    redirect: "/tickets",
  },
  {
    path: "/canned-responses",
    name: "CannedResponses",
    component: () => import("@/pages/CannedResponses.vue"),
  },
  {
    path: "/dashboard",
    name: "Dashboard",
    component: () => import("@/pages/dashboard/Dashboard.vue"),
  },
  {
    path: "/call-logs",
    name: "CallLogs",
    component: () => import("@/pages/call-logs/CallLogs.vue"),
  },
  {
    path: "/settings",
    name: "Settings",
    redirect: "/settings/profile",
  },
  {
    path: "/settings/profile",
    name: "Profile",
    component: () => import("@/pages/settings/Profile/Profile.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/general",
    name: "GeneralSettings",
    component: () => import("@/pages/settings/General/General.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-notifications",
    name: "EmailNotificationsSettings",
    component: () =>
      import("@/pages/settings/EmailNotifications/EmailNotifications.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-notifications/share-feedback",
    name: "NotificationSettings/ShareFeedback",
    component: () =>
      import("@/pages/settings/EmailNotifications/ShareFeedback.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-notifications/acknowledgement",
    name: "NotificationSettings/Acknowledgement",
    component: () =>
      import("@/pages/settings/EmailNotifications/Acknowledgement.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-notifications/reply-from-agent",
    name: "NotificationSettings/ReplyFromAgent",
    component: () =>
      import("@/pages/settings/EmailNotifications/ReplyFromAgent.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-notifications/reply-from-contact",
    name: "NotificationSettings/ReplyFromContact",
    component: () =>
      import("@/pages/settings/EmailNotifications/ReplyFromContact.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/teams",
    name: "SettingsTeams",
    component: () => import("@/pages/settings/Teams/Teams.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/teams/new",
    name: "NewSettingsTeam",
    component: () => import("@/pages/settings/Teams/NewTeam.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/teams/:id",
    name: "EditSettingsTeam",
    component: () => import("@/pages/settings/Teams/EditTeam.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-accounts",
    name: "EmailAccounts",
    component: () => import("@/pages/settings/EmailAccount/EmailAccount.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-accounts/new",
    name: "NewEmailAccount",
    component: () =>
      import("@/pages/settings/EmailAccount/NewEmailAccount.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/email-accounts/:id",
    name: "EditEmailAccount",
    component: () =>
      import("@/pages/settings/EmailAccount/EditEmailAccount.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/sla-policies",
    name: "SLAPolicies",
    component: () => import("@/pages/settings/Sla/Sla.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/sla-policies/new",
    name: "NewSLAPolicy",
    component: () => import("@/pages/settings/Sla/NewSlaPolicy.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/sla-policies/:id",
    name: "EditSLAPolicy",
    component: () => import("@/pages/settings/Sla/EditSlaPolicy.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/telephony",
    name: "TelephonySettings",
    component: () => import("@/pages/settings/Telephony/Telephony.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/invite-agent",
    name: "InviteAgent",
    component: () => import("@/pages/settings/InviteAgent.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/agents",
    name: "Agents",
    component: () => import("@/pages/settings/Agents/Agents.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/agents/:id",
    name: "Agent",
    component: () => import("@/pages/settings/Agents/Agents.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/holiday-list",
    name: "BusinessHolidays",
    component: () => import("@/pages/settings/Holiday/Holiday.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/holiday-list/new",
    name: "NewBusinessHolidays",
    component: () => import("@/pages/settings/Holiday/NewHolidayList.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/holiday-list/:id",
    name: "EditBusinessHolidays",
    component: () => import("@/pages/settings/Holiday/EditHolidayList.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/assignment-rules",
    name: "AssignmentRules",
    component: () =>
      import("@/pages/settings/AssignmentRule/AssignmentRule.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/assignment-rules/new",
    name: "NewAssignmentRule",
    component: () =>
      import("@/pages/settings/AssignmentRule/NewAssignmentRule.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/assignment-rules/:id",
    name: "EditAssignmentRule",
    component: () =>
      import("@/pages/settings/AssignmentRule/EditAssignmentRule.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/field-dependencies",
    name: "FieldDependencies",
    component: () =>
      import("@/pages/settings/FieldDependency/FieldDependency.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/field-dependencies/new",
    name: "NewFieldDependency",
    component: () =>
      import("@/pages/settings/FieldDependency/NewFieldDependency.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },
  {
    path: "/settings/field-dependencies/:id",
    name: "EditFieldDependency",
    component: () =>
      import("@/pages/settings/FieldDependency/EditFieldDependency.vue"),
    props: true,
    meta: {
      auth: true,
    },
  },

  // Customer Portal Routes
  {
    path: "/my-tickets",
    name: "TicketsCustomer",
    component: () => import("@/pages/ticket/Tickets.vue"),
    meta: {
      public: true,
      auth: true,
    },
  },
  {
    path: "/my-tickets/:ticketId",
    name: "TicketCustomer",
    component: () => import("@/pages/ticket/TicketCustomer.vue"),
    meta: {
      public: true,
      auth: true,
    },
    props: true,
  },
  {
    path: "/my-tickets/new",
    name: "TicketNew",
    component: () => import("@/pages/ticket/TicketNew.vue"),
    props: true,
    meta: {
      onSuccessRoute: "TicketCustomer",
      parent: "TicketsCustomer",
      public: true,
      auth: true,
    },
  },
  {
    path: "/kb-public",
    name: "CustomerKnowledgeBase",
    component: () => import("@/pages/knowledge-base/KnowledgeBaseCustomer.vue"),
    meta: {
      public: true,
      auth: true,
    },
  },
  {
    path: "/kb-public/:categoryId",
    name: "Articles",
    component: () => import("@/pages/knowledge-base/Articles.vue"),
    props: true,
    meta: {
      public: true,
      auth: true,
    },
  },
  {
    path: "/kb-public/articles/:articleId",
    name: "ArticlePublic",
    component: () => import("@/pages/knowledge-base/Article.vue"),
    props: true,
    meta: {
      public: true,
      auth: true,
    },
  },

  // Additonal routes
  {
    path: "/:pathMatch(.*)*",
    name: "Invalid Page",
    component: () => import("@/pages/InvalidPage.vue"),
  },
];

const handleMobileView = (componentName) => {
  return isMobileView.value ? `Mobile${componentName}` : componentName;
};

export const router = createRouter({
  history: createWebHistory("/helpdesk/"),
  routes,
});

router.beforeEach(async (to, _, next) => {
  const authStore = useAuthStore();
  isCustomerPortal.value = to.meta.public || false;
  if (authStore.isLoggedIn) {
    await authStore.init();
  }

  if (!authStore.isLoggedIn) {
    window.location.href = LOGIN_PAGE;
  } else if (!to.meta.public && !authStore.hasDeskAccess) {
    next({ name: "TicketsCustomer" });
  } else if (to.name === "TicketAgent" && !authStore.isAgent) {
    const ticketId = to.params.ticketId;
    next({
      name: "TicketCustomer",
      params: { ticketId },
    });
  } else {
    next();
  }
});

router.afterEach(async (to) => {
  if (to.meta.public) return;
  const { users } = useUserStore();
  if (!users?.fetched) {
    await users.fetch();
  }
});
