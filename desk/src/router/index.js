import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { init as initTelemetry } from "@/telemetry";
import { AuthPages } from "./auth";
import { CustomerPages } from "./customer";
import { KnowldegeBasePages } from "./knowledege-base";
import { getPage } from "./utils";

export const WEBSITE_ROOT = "Website Root";

export const LOGIN = "AuthLogin";
export const SIGNUP = "AuthSignup";
export const VERIFY = "AuthVerify";
export const AUTH_ROUTES = [LOGIN, SIGNUP, VERIFY];
export const ONBOARDING_PAGE = "Setup";

export const CUSTOMER_PORTAL_NEW_TICKET = "TicketNew";
export const CUSTOMER_PORTAL_TICKET = "TicketCustomer";

export const AGENT_PORTAL_AGENT_LIST = "AgentList";
export const AGENT_PORTAL_CONTACT_LIST = "ContactList";
export const AGENT_PORTAL_CUSTOMER_LIST = "CustomerList";
export const AGENT_PORTAL_DASHBOARD = "DeskDashboard";
export const AGENT_PORTAL_ESCALATION_RULE_LIST = "EscalationRules";
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

export const KB_PUBLIC = "KBHome";
export const KB_PUBLIC_ARTICLE = "KBArticlePublic";
export const KB_PUBLIC_CATEGORY = "KBCategoryPublic";

export const CUSTOMER_PORTAL_LANDING = "TicketsCustomer";
export const AGENT_PORTAL_LANDING = AGENT_PORTAL_TICKET_LIST;

const routes = [
  {
    path: "",
    component: () => getPage("HRoot"),
  },
  AuthPages,
  CustomerPages,
  KnowldegeBasePages,
  {
    path: "/onboarding",
    name: ONBOARDING_PAGE,
    component: () => import("@/pages/onboarding/SimpleOnboarding.vue"),
  },
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
          parent: "TicketsAgent",
        },
      },
      {
        path: "tickets/:ticketId",
        name: AGENT_PORTAL_TICKET,
        component: () => getPage("TicketAgent2"),
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
        path: "canned-responses",
        name: "CannedResponses",
        component: () => import("@/pages/CannedResponses.vue"),
      },
      {
        path: "canned-responses/:id",
        name: "CannedResponse",
        component: () => import("@/pages/CannedResponse.vue"),
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
  const usersStore = useUserStore();

  try {
    await initTelemetry();
    await authStore.init();
    await usersStore.init();

    if ((to.meta.agent && !authStore.hasDeskAccess) || isAuthRoute) {
      router.replace({ name: WEBSITE_ROOT });
    }
  } catch {
    if (!isAuthRoute) {
      router.replace({
        name: LOGIN,
        query: {
          redirect: to.path.toString(),
        },
      });
    }
  }
});
