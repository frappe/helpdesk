import { createRouter, createWebHistory } from "vue-router"

const routes = [
	{
		path: "/frappedesk/login",
		name: "DeskLogin",
		component: () => import("@/pages/auth/Login.vue"),
	},
	{
		path: "/support/login",
		name: "PortalLogin",
		component: () => import("@/pages/auth/Login.vue"),
	},
	{
		path: "/frappedesk/signup",
		name: "DeskSignup",
		component: () => import("@/pages/auth/Signup.vue"),
	},
	{
		path: "/support/signup",
		name: "PortalSignup",
		component: () => import("@/pages/auth/Signup.vue"),
	},
	{
		path: "/support/verify/:requestKey",
		name: "Verify Account",
		component: () =>
			import(
				/* webpackChunkName: "setup-account" */ "@/pages/auth/VerifyAccount.vue"
			),
		props: true,
	},
	{
		path: "/frappedesk/setup",
		name: "DeskSetup",
		component: () => import("@/pages/desk/Setup.vue"),
	},
	{
		path: "/frappedesk",
		name: "Desk",
		component: () => import("@/pages/desk/Desk.vue"),
		children: [
			{
				path: "",
				redirect: () => {
					return { path: "/frappedesk/tickets" }
				},
			},
			{
				path: "tickets",
				name: "DeskTickets",
				component: () => import("@/pages/desk/Tickets.vue"),
			},
			{
				path: "tickets/:ticketId",
				name: "DeskTicket",
				component: () => import("@/pages/desk/Ticket.vue"),
				props: true,
				meta: {
					breadcrumbs(route) {
						return [
							{
								label: "Tickets",
								path: "/frappedesk/tickets",
							},
							{
								label: route.params.ticketId,
							},
						]
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
						component: () =>
							import("@/pages/common/kb/Category.vue"), // shows root categories and faqs
						meta: {
							editable: true,
							isRoot: true,
						},
					},
					{
						path: "categories/:categoryId",
						name: "DeskKBCategory", // Category Page
						component: () =>
							import("@/pages/common/kb/Category.vue"), // shows sub categories and articles
						props: true,
						meta: {
							editable: true,
						},
					},
					{
						path: "articles",
						name: "DeskKBArticles",
						component: () => import("@/pages/desk/kb/Articles.vue"), // Articles.vue - shows all articles
					},
					{
						path: "articles/:articleId",
						name: "DeskKBArticle", // Article Edit page
						component: () =>
							import("@/pages/common/kb/Article.vue"), // Article.vue - article edit page
						props: true,
						meta: {
							editable: true,
						},
					},
					{
						path: "articles/new",
						name: "DeskKBArticleNew", // Article Edit page
						component: () =>
							import("@/pages/common/kb/Article.vue"), // Article.vue - article edit page
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
								path: "/frappedesk/contacts",
							},
							{
								label: route.params.contactId,
							},
						]
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
							return { path: "/frappedesk/settings/agents" }
						},
					},
					{
						path: "agents",
						name: "Agents",
						component: () =>
							import("@/pages/desk/settings/agent/Agents.vue"),
					},
					{
						path: "agents/:agentId",
						name: "Agent",
						component: () =>
							import("@/pages/desk/settings/agent/Agent.vue"),
						props: true,
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
						component: () =>
							import("@/pages/desk/settings/sla/SlaPolicy.vue"),
					},
					{
						path: "sla/:slaId",
						name: "SlaPolicy",
						component: () =>
							import("@/pages/desk/settings/sla/SlaPolicy.vue"),
						props: true,
					},
					{
						path: "emails",
						name: "Emails",
						component: () =>
							import("@/pages/desk/settings/email/Emails.vue"),
					},
					{
						path: "emails/new",
						name: "NewEmailAccount",
						component: () =>
							import(
								"@/pages/desk/settings/email/EmailAccount.vue"
							),
					},
					{
						path: "emails/:emailAccountId",
						name: "EmailAccount",
						component: () =>
							import(
								"@/pages/desk/settings/email/EmailAccount.vue"
							),
						props: true,
					},
				],
			},
		],
	},
	{
		path: "/support",
		name: "Portal",
		component: () => import("@/pages/portal/Portal.vue"),
		children: [
			{
				path: "tickets",
				name: "ProtalTickets",
				component: () => import("@/pages/portal/Tickets.vue"),
			},
			{
				path: "tickets/:ticketId",
				name: "PortalTicket",
				component: () => import("@/pages/portal/Ticket.vue"),
				props: true,
			},
			{
				path: "tickets/new/:templateId",
				name: "TemplatedNewTicket",
				component: () => import("@/pages/portal/NewTicket.vue"),
				props: true,
			},
			{
				path: "tickets/new",
				name: "DefaultNewTicket",
				component: () => import("@/pages/portal/NewTicket.vue"),
			},
			{
				path: "impersonate",
				name: "Impersonate",
				component: () => import("@/pages/portal/Impersonate.vue"),
			},
			{
				path: "kb",
				name: "PortalKB",
				component: () => import("@/pages/portal/KnowledgeBase.vue"),
				children: [
					{
						path: "",
						name: "PortalKBHome",
						component: () =>
							import("@/pages/common/kb/Category.vue"), // shows root categories and faqs
						meta: {
							editable: false,
							isRoot: true,
						},
					},
					{
						path: "categories/:categoryId",
						name: "PortalKBCategory", // Category Page
						component: () =>
							import("@/pages/common/kb/Category.vue"), // shows sub categories and articles
						props: true,
						meta: {
							editable: false,
						},
					},
					{
						path: "articles/:articleId",
						name: "PortalKBArticle",
						component: () =>
							import("@/pages/common/kb/Article.vue"),
						props: true,
						meta: {
							editable: false,
						},
					},
				],
			},
		],
	},
]

let router = createRouter({
	history: createWebHistory("/"),
	routes,
})

export default router
