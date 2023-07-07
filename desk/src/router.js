import { createRouter, createWebHistory } from "vue-router";
import { call } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { init as initTelemetry } from "./telemetry";

export const WEBSITE_ROOT = "Website Root";

export const LOGIN = "Login";
export const SIGNUP = "Signup";
export const VERIFY = "Verify Account";
export const AUTH_ROUTES = [LOGIN, SIGNUP, VERIFY];
export const ONBOARDING_PAGE = "Setup";

export const CUSTOMER_PORTAL_NEW_TICKET = "DefaultNewTicket";
export const CUSTOMER_PORTAL_TICKET = "PortalTicket";

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
export const AGENT_PORTAL_TICKET = "DeskTicket";
export const AGENT_PORTAL_TICKET_LIST = "DeskTickets";
export const AGENT_PORTAL_TICKET_TYPE_LIST = "TicketTypes";
export const AGENT_PORTAL_TICKET_TYPE_NEW = "NewTicketType";
export const AGENT_PORTAL_TICKET_TYPE_SINGLE = "TicketType";

export const KB_PUBLIC = "Knowledge Base";
export const KB_PUBLIC_ARTICLE = "PortalKBArticle";

export const CUSTOMER_PORTAL_LANDING = "PortalTickets";
export const AGENT_PORTAL_LANDING = AGENT_PORTAL_TICKET_LIST;

const routes = [
  {
    path: "",
    name: WEBSITE_ROOT,
    component: () => import("@/pages/WebsiteRoot.vue"),
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
    component: () => import("@/pages/portal/kb/KnowledgeBase.vue"),
    children: [
      {
        path: "",
        name: KB_PUBLIC,
        component: () =>
          // shows root categories and faqs
          import("@/pages/common/kb/Category.vue"),
        meta: {
          editable: false,
          isRoot: true,
        },
      },
      {
        path: "categories/:categoryId",
        name: "PortalKBCategory", // Category Page
        component: () =>
          // shows sub categories and articles
          import("@/pages/common/kb/Category.vue"),
        props: true,
        meta: {
          editable: false,
        },
      },
      {
        path: "articles/:articleId/:articleTitleSlug",
        name: KB_PUBLIC_ARTICLE,
        component: () => import("@/pages/common/kb/Article.vue"),
        props: true,
        meta: {
          editable: false,
        },
      },
    ],
  },
  {
    path: "/my-tickets",
    component: () => import("@/pages/portal/CustomerRoot.vue"),
    children: [
      {
        path: "",
        name: CUSTOMER_PORTAL_LANDING,
        component: () => import("@/pages/portal/TicketList.vue"),
      },
      {
        path: ":ticketId",
        name: CUSTOMER_PORTAL_TICKET,
        component: () => import("@/pages/portal/TicketSingle.vue"),
        props: true,
      },
      {
        path: "new",
        name: CUSTOMER_PORTAL_NEW_TICKET,
        component: () => import("@/pages/portal/TicketNew.vue"),
      },
      {
        path: "new/:templateId",
        component: () => import("@/pages/portal/TicketNew.vue"),
        props: true,
      },
    ],
  },
  {
    path: "",
    name: "AgentRoot",
    component: () => import("@/pages/desk/AgentRoot.vue"),
    children: [
      {
        path: "dashboard",
        name: AGENT_PORTAL_DASHBOARD,
        component: () => import("@/pages/desk/DeskDashboard.vue"),
      },
      {
        path: "tickets",
        name: AGENT_PORTAL_TICKET_LIST,
        component: () => import("@/pages/desk/ticket-list/TicketList.vue"),
      },
      {
        path: "tickets/:ticketId",
        name: AGENT_PORTAL_TICKET,
        component: () => import("@/pages/desk/ticket/TicketSingle.vue"),
        props: true,
        meta: {
          breadcrumbs(route) {
            return [
              {
                label: "Tickets",
                path: "/helpdesk/tickets",
              },
              {
                label: route.params.ticketId,
              },
            ];
          },
        },
      },
      {
        path: "kb",
        name: "DeskKB",
        component: () => import("@/pages/desk/kb/KnowledgeBase.vue"),
        children: [
          {
            path: "",
            name: "DeskKBHome",
            // shows root categories and faqs
            component: () => import("@/pages/common/kb/Category.vue"),
            meta: {
              editable: true,
              isRoot: true,
            },
          },
          {
            path: "categories/:categoryId",
            // Category Page
            name: "DeskKBCategory",
            component: () =>
              // shows sub categories and articles
              import("@/pages/common/kb/Category.vue"),
            props: true,
            meta: {
              editable: true,
            },
          },
          {
            path: "articles",
            name: "DeskKBArticles",
            // Articles.vue - shows all articles
            component: () => import("@/pages/desk/kb/Articles.vue"),
          },
          {
            path: "articles/:articleId",
            // Article Edit page
            name: "DeskKBArticle",
            component: () =>
              // Article.vue - article edit page
              import("@/pages/common/kb/Article.vue"),
            props: true,
            meta: {
              editable: true,
            },
          },
          {
            path: "articles/new",
            // Article Edit page
            name: "DeskKBArticleNew",
            component: () =>
              // Article.vue - article edit page
              import("@/pages/common/kb/Article.vue"),
            props: true,
            meta: {
              editable: true,
              editMode: true,
              isNew: true,
            },
          },
        ],
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
  // go to article page only if the article is published
  if (to.name === "PortalKBArticle") {
    const articleIsPublished = await call(
      "helpdesk.api.kb.check_if_article_is_published",
      { article_name: to.params.articleId }
    );
    if (!articleIsPublished) {
      return { name: "PortalKBHome" };
    }
  }

  return true;
});

router.beforeEach(async (to) => {
  const isAuthRoute = AUTH_ROUTES.includes(to.name);
  const authStore = useAuthStore();

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
