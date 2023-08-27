import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { init as initTelemetry } from "@/telemetry";
import { CustomerPages } from "./customer";
import { getPage } from "./utils";

export const WEBSITE_ROOT = "Website Root";

export const LOGIN = "Login";
export const SIGNUP = "Signup";
export const VERIFY = "Verify Account";
export const AUTH_ROUTES = [LOGIN, SIGNUP, VERIFY];
export const ONBOARDING_PAGE = "Setup";

export const CUSTOMER_PORTAL_NEW_TICKET = "TicketNew";
export const CUSTOMER_PORTAL_TICKET = "TicketCustomer";

export const AGENT_PORTAL_AGENT_LIST = "AgentList";
export const AGENT_PORTAL_CANNED_RESPONSE_LIST = "CannedResponses";
export const AGENT_PORTAL_CANNED_RESPONSE_SINGLE = "CannedResponse";
export const AGENT_PORTAL_CONTACT_LIST = "ContactList";
export const AGENT_PORTAL_CUSTOMER_LIST = "CustomerList";
export const AGENT_PORTAL_DASHBOARD = "DeskDashboard";
export const AGENT_PORTAL_EMAIL_LIST = "Emails";
export const AGENT_PORTAL_EMAIL_NEW = "NewEmailAccount";
export const AGENT_PORTAL_EMAIL_SINGLE = "EmailAccount";
export const AGENT_PORTAL_ESCALATION_RULE_LIST = "EscalationRules";
export const AGENT_PORTAL_SLA_LIST = "SlaPolicies";
export const AGENT_PORTAL_SLA_NEW = "NewSlaPolicy";
export const AGENT_PORTAL_SLA_SINGLE = "SlaPolicy";
export const AGENT_PORTAL_TEAM_LIST = "Teams";
export const AGENT_PORTAL_TEAM_SINGLE = "Team";
export const AGENT_PORTAL_TICKET = "TicketAgent";
export const AGENT_PORTAL_TICKET_LIST = "TicketsAgent";
export const AGENT_PORTAL_TICKET_TYPE_LIST = "TicketTypes";
export const AGENT_PORTAL_TICKET_TYPE_NEW = "NewTicketType";
export const AGENT_PORTAL_TICKET_TYPE_SINGLE = "TicketType";
export const AGENT_PORTAL_KNOWLEDGE_BASE = "DeskKBHome";
export const AGENT_PORTAL_KNOWLEDGE_BASE_CATEGORY = "DeskKBCategory";
export const AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY = "DeskKBSubcategory";
export const AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE = "DeskKBArticle";

export const KB_PUBLIC = "KBPublic";
export const KB_PUBLIC_ARTICLE = "KBArticlePublic";
export const KB_PUBLIC_CATEGORY = "PortalKBCategory";

export const CUSTOMER_PORTAL_LANDING = "TicketsCustomer";
export const AGENT_PORTAL_LANDING = AGENT_PORTAL_TICKET_LIST;

const routes = [
  {
    path: "",
    component: () => getPage("HRoot"),
  },
  {
    path: "/login",
    name: LOGIN,
    component: () => import("@/pages/auth/AuthLogin.vue"),
  },
  {
    path: "/signup",
    name: SIGNUP,
    component: () => import("@/pages/auth/AuthSignup.vue"),
  },
  {
    path: "/verify/:requestKey",
    name: VERIFY,
    component: () => import("@/pages/auth/AuthVerify.vue"),
    props: true,
  },
  {
    path: "/onboarding",
    name: ONBOARDING_PAGE,
    component: () => import("@/pages/onboarding/SimpleOnboarding.vue"),
  },
  {
    path: "/knowledge-base",
    component: () => import("@/pages/knowledge-base/KnowledgeBasePublic.vue"),
    children: [
      {
        path: "",
        name: KB_PUBLIC,
        component: () =>
          import("@/pages/knowledge-base/KnowledgeBasePublicHome.vue"),
      },
      {
        path: ":categoryId",
        name: KB_PUBLIC_CATEGORY,
        component: () =>
          import("@/pages/knowledge-base/KnowledgeBasePublicCategory.vue"),
        props: true,
      },
      {
        path: "articles/:articleId",
        name: KB_PUBLIC_ARTICLE,
        component: () =>
          import("@/pages/knowledge-base/KnowledgeBaseArticle.vue"),
        props: (route) => ({
          ...route.params,
          isPublic: true,
        }),
      },
    ],
  },
  CustomerPages,
  {
    path: "",
    name: "AgentRoot",
    component: () => import("@/pages/desk/AgentRoot.vue"),
    meta: {
      auth: true,
      agent: true,
      admin: false,
    },
    children: [
      {
        path: "dashboard",
        name: AGENT_PORTAL_DASHBOARD,
        component: () => import("@/pages/desk/DeskDashboard.vue"),
      },
      {
        path: "tickets",
        name: AGENT_PORTAL_TICKET_LIST,
        component: () => getPage("TicketsAgent"),
      },
      {
        path: "tickets/new/:templateId?",
        name: "TicketAgentNew",
        component: () => getPage("TicketNew"),
        props: true,
        meta: {
          onSuccessRoute: "TicketAgent",
        },
      },
      {
        path: "tickets/:ticketId",
        name: AGENT_PORTAL_TICKET,
        component: () => getPage("TicketAgent"),
        props: true,
      },
      {
        path: "kb",
        name: AGENT_PORTAL_KNOWLEDGE_BASE,
        component: () => import("@/pages/knowledge-base/KnowledgeBase.vue"),
        children: [
          {
            path: ":categoryId",
            name: AGENT_PORTAL_KNOWLEDGE_BASE_CATEGORY,
            props: true,
            component: () =>
              import("@/pages/knowledge-base/KnowledgeBaseCategory.vue"),
          },
          {
            path: ":categoryId/:subCategoryId",
            name: AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY,
            props: true,
            component: () =>
              import("@/pages/knowledge-base/KnowledgeBaseSubcategory.vue"),
          },
        ],
      },
      {
        path: "kb/articles/:articleId",
        name: AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
        props: true,
        component: () =>
          import("@/pages/knowledge-base/KnowledgeBaseArticle.vue"),
      },
      {
        path: "customers",
        name: AGENT_PORTAL_CUSTOMER_LIST,
        component: () => import("@/pages/desk/customer/CustomerList.vue"),
      },
      {
        path: "contacts",
        name: AGENT_PORTAL_CONTACT_LIST,
        component: () => import("@/pages/desk/contact/ContactList.vue"),
      },
      {
        path: "agents",
        name: AGENT_PORTAL_AGENT_LIST,
        component: () => import("@/pages/desk/agent/AgentList.vue"),
      },
      {
        path: "teams",
        name: AGENT_PORTAL_TEAM_LIST,
        component: () => import("@/pages/desk/team/TeamList.vue"),
      },
      {
        path: "teams/:teamId",
        name: AGENT_PORTAL_TEAM_SINGLE,
        component: () => import("@/pages/desk/team/TeamSingle.vue"),
        props: true,
      },
      {
        path: "ticket-types",
        name: AGENT_PORTAL_TICKET_TYPE_LIST,
        component: () => import("@/pages/desk/ticket_type/TicketTypeList.vue"),
      },
      {
        path: "ticket-types/:id",
        name: AGENT_PORTAL_TICKET_TYPE_SINGLE,
        component: () => import("@/pages/desk/ticket_type/TicketType.vue"),
        props: true,
      },
      {
        path: "ticket-types/new",
        name: AGENT_PORTAL_TICKET_TYPE_NEW,
        component: () => import("@/pages/desk/ticket_type/TicketType.vue"),
      },
      {
        path: "sla",
        name: AGENT_PORTAL_SLA_LIST,
        component: () => import("@/pages/desk/sla/SlaList.vue"),
      },
      {
        path: "sla/new",
        name: AGENT_PORTAL_SLA_NEW,
        component: () => import("@/pages/desk/sla/SlaPolicy.vue"),
      },
      {
        path: "sla/:id",
        name: AGENT_PORTAL_SLA_SINGLE,
        component: () => import("@/pages/desk/sla/SlaPolicy.vue"),
        props: true,
      },
      {
        path: "canned-responses",
        name: AGENT_PORTAL_CANNED_RESPONSE_LIST,
        component: () =>
          import("@/pages/desk/canned_response/CannedResponseList.vue"),
      },
      {
        path: "canned-responses/:id",
        name: AGENT_PORTAL_CANNED_RESPONSE_SINGLE,
        component: () =>
          import("@/pages/desk/canned_response/CannedResponseSingle.vue"),
        props: true,
      },
      {
        path: "emails",
        name: AGENT_PORTAL_EMAIL_LIST,
        component: () => import("@/pages/desk/email/EmailList.vue"),
      },
      {
        path: "emails/new",
        name: AGENT_PORTAL_EMAIL_NEW,
        component: () => import("@/pages/desk/email/EmailAccount.vue"),
      },
      {
        path: "emails/:emailAccountId",
        name: AGENT_PORTAL_EMAIL_SINGLE,
        component: () => import("@/pages/desk/email/EmailAccount.vue"),
        props: true,
      },
      {
        path: "escalation-rules",
        name: AGENT_PORTAL_ESCALATION_RULE_LIST,
        component: () =>
          import("@/pages/desk/escalation/EscalationRuleList.vue"),
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory("/helpdesk/"),
  routes,
});

router.beforeEach(async (to) => {
  const isAuthRoute = AUTH_ROUTES.includes(to.name);
  const authStore = useAuthStore();
  useUserStore();

  try {
    await initTelemetry();
    await authStore.init();

    if (isAuthRoute) {
      router.replace({ name: WEBSITE_ROOT });
    }
  } catch {
    if (!isAuthRoute) {
      router.replace({ name: LOGIN });
    }
  }
});
