import { createRouter, createWebHistory } from "vue-router";
import { call } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";

export const LOGIN = "Login";
export const SIGNUP = "Signup";
export const VERIFY = "Verify Account";
export const AGENT_PORTAL_LANDING = "DeskTickets";
export const CUSTOMER_PORTAL_LANDING = "PortalTickets";
export const AUTH_BYPASS_ROUTES = [LOGIN, SIGNUP, VERIFY];
export const AGENT_PORTAL_TICKET = "DeskTicket";

const routes = [
	{
		path: "",
		component: () => import("@/pages/WebsiteRoot.vue"),
	},
	{
		path: "/login",
		name: LOGIN,
		component: () => import("@/pages/auth/Login.vue"),
	},
	{
		path: "/signup",
		name: SIGNUP,
		component: () => import("@/pages/auth/Signup.vue"),
	},
	{
		path: "/verify/:requestKey",
		name: VERIFY,
		component: () =>
			import(
				/* webpackChunkName: "setup-account" */ "@/pages/auth/VerifyAccount.vue"
			),
		props: true,
	},
	{
		path: "",
		name: "PortalRoot",
		component: () => import("@/pages/portal/Portal.vue"),
		children: [
			{
				path: "my-tickets",
				name: "Ticketing",
				component: () => import("@/pages/portal/ticketing/Ticketing.vue"),
				children: [
					{
						path: "",
						name: CUSTOMER_PORTAL_LANDING,
						component: () => import("@/pages/portal/ticketing/Tickets.vue"),
					},
					{
						path: ":ticketId",
						name: "PortalTicket",
						component: () => import("@/pages/portal/ticketing/Ticket.vue"),
						props: true,
					},
					{
						path: "new/:templateId",
						name: "TemplatedNewTicket",
						component: () => import("@/pages/portal/ticketing/NewTicket.vue"),
						props: true,
					},
					{
						path: "new",
						name: "DefaultNewTicket",
						component: () => import("@/pages/portal/ticketing/NewTicket.vue"),
					},
					{
						path: "impersonate",
						name: "Impersonate",
						component: () => import("@/pages/portal/ticketing/Impersonate.vue"),
					},
				],
			},
			{
				path: "knowledge-base",
				name: "PortalBK",
				component: () => import("@/pages/portal/kb/KnowledgeBase.vue"),
				children: [
					{
						path: "",
						name: "PortalKBHome",
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
						name: "PortalKBArticle",
						component: () => import("@/pages/common/kb/Article.vue"),
						props: true,
						meta: {
							editable: false,
						},
					},
				],
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
				name: "Dashboard",
				component: () => import("@/pages/desk/Dashboard.vue"),
			},
			{
				path: "tickets",
				name: AGENT_PORTAL_LANDING,
				component: () => import("@/pages/desk/Tickets.vue"),
			},
			{
				path: "tickets/:ticketId",
				name: AGENT_PORTAL_TICKET,
				component: () => import("@/pages/desk/ticket/TicketNeo.vue"),
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
				name: "Customers",
				component: () => import("@/pages/desk/Customers.vue"),
			},
			{
				path: "customers/:customerId",
				name: "Customer",
				component: () => import("@/pages/desk/Customer.vue"),
				props: true,
			},
			{
				path: "contacts",
				name: "Contacts",
				component: () => import("@/pages/desk/Contacts.vue"),
			},
			{
				path: "contacts/:contactId",
				name: "Contact",
				component: () => import("@/pages/desk/Contact.vue"),
				props: true,
				meta: {
					breadcrumbs(route) {
						return [
							{
								label: "Contacts",
								path: "/helpdesk/contacts",
							},
							{
								label: route.params.contactId,
							},
						];
					},
				},
			},
			{
				path: "settings",
				name: "Settings",
				component: () => import("@/pages/desk/settings/Settings.vue"),
				children: [
					{
						path: "",
						redirect: () => {
							return { path: "/helpdesk/settings/agents" };
						},
					},
					{
						path: "agents",
						name: "Agents",
						component: () => import("@/pages/desk/settings/agent/Agents.vue"),
					},
					{
						path: "agents/:agentId",
						name: "Agent",
						component: () => import("@/pages/desk/settings/agent/Agent.vue"),
						props: true,
					},
					{
						path: "teams",
						name: "Teams",
						component: () => import("@/pages/desk/settings/team/Teams.vue"),
					},
					{
						path: "teams/:teamId",
						name: "Team",
						component: () => import("@/pages/desk/settings/team/Team.vue"),
						props: true,
					},
					{
						path: "teams/new",
						name: "NewTeam",
						component: () => import("@/pages/desk/settings/team/Team.vue"),
					},
					{
						path: "ticket_types",
						name: "TicketTypes",
						component: () =>
							import("@/pages/desk/settings/ticket_type/TicketTypes.vue"),
					},
					{
						path: "ticket_types/:ticketTypeId",
						name: "TicketType",
						component: () =>
							import("@/pages/desk/settings/ticket_type/TicketType.vue"),
						props: true,
					},
					{
						path: "ticket_types/new",
						name: "NewTicketType",
						component: () =>
							import("@/pages/desk/settings/ticket_type/TicketType.vue"),
					},
					{
						path: "sla",
						name: "SlaPolicies",
						component: () =>
							import("@/pages/desk/settings/sla/SlaPolicies.vue"),
					},
					{
						path: "sla/new",
						name: "NewSlaPolicy",
						component: () => import("@/pages/desk/settings/sla/SlaPolicy.vue"),
					},
					{
						path: "sla/:slaId",
						name: "SlaPolicy",
						component: () => import("@/pages/desk/settings/sla/SlaPolicy.vue"),
						props: true,
					},
					{
						path: "canned_response",
						name: "CannedResponses",
						component: () =>
							import(
								"@/pages/desk/settings/canned_response/CannedResponses.vue"
							),
					},
					{
						path: "canned_responses/:canned_responseId",
						name: "CannedResponse",
						component: () =>
							import(
								"@/pages/desk/settings/canned_response/CannedResponse.vue"
							),
						props: true,
					},
					{
						path: "emails",
						name: "Emails",
						component: () => import("@/pages/desk/settings/email/Emails.vue"),
					},
					{
						path: "emails/new",
						name: "NewEmailAccount",
						component: () =>
							import("@/pages/desk/settings/email/EmailAccount.vue"),
					},
					{
						path: "emails/:emailAccountId",
						name: "EmailAccount",
						component: () =>
							import("@/pages/desk/settings/email/EmailAccount.vue"),
						props: true,
					},
				],
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
	if (AUTH_BYPASS_ROUTES.includes(to.name)) return;

	const authStore = useAuthStore();
	await authStore.init().catch(() => router.replace({ name: LOGIN }));
});
