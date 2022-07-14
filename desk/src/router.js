import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/frappedesk/login',
		name: 'DeskLogin',
		component: () => import('@/pages/auth/Login.vue'),
	},
	{
		path: '/support/login',
		name: 'PortalLogin',
		component: () => import('@/pages/auth/Login.vue'),
	},
	{
		path: '/frappedesk/signup',
		name: 'DeskSignup',
		component: () => import('@/pages/auth/Signup.vue')
	},
	{
		path: '/support/signup',
		name: 'PortalSignup',
		component: () => import('@/pages/auth/Signup.vue')
	},
	{
		path: '/support/verify/:requestKey',
		name: 'Verify Account',
		component: () =>
			import(
				/* webpackChunkName: "setup-account" */ '@/pages/auth/VerifyAccount.vue'
			),
		props: true,
	},
	{
		path: '/frappedesk/setup',
		name: 'DeskSetup',
		component: () => import('@/pages/desk/Setup.vue'),
	},
	{
		path: '/frappedesk',
		name: 'Desk',
		component: () => import('@/pages/desk/Desk.vue'),
		children: [
			{
				path: '',
				redirect: () => {
					return { path: '/frappedesk/tickets'}
				},
			},
			{
				path: 'tickets',
				name: 'DeskTickets',
				component: () => import('@/pages/desk/Tickets.vue'),
			},
			{
				path: 'tickets/:ticketId',
				name: 'DeskTicket',
				component: () => import('@/pages/desk/Ticket.vue'),
				props: true,
				meta: {
					breadcrumbs(route) {
						return [
							{
								label: 'Tickets',
								path: '/frappedesk/tickets'
							},
							{
								label: route.params.ticketId
							}
						]
					}
				}
			},
			{
				path: 'contacts',
				name: 'Contacts',
				component: () => import('@/pages/desk/Contacts.vue')
			},
			{
				path: 'contacts/:contactId',
				name: 'Contact',
				component: () => import('@/pages/desk/Contact.vue'),
				props: true,
				meta: {
					breadcrumbs(route) {
						return [
							{
								label: 'Contacts',
								path: '/frappedesk/contacts'
							},
							{
								label: route.params.contactId
							}
						]
					}
				}
			},
			{
				path: 'settings',
				name: 'Settings',
				component: () => import('@/pages/desk/settings/Settings.vue'),
				children: [
					{
						path: '',
						redirect: () => {
							return { path: '/frappedesk/settings/agents'}
						},
					},
					{
						path: 'agents',
						name: 'Agents',
						component: () => import('@/pages/desk/settings/agent/Agents.vue')
					},
					{
						path: 'agents/:agentId',
						name: 'Agent',
						component: () => import('@/pages/desk/settings/agent/Agent.vue'),
						props: true
					},
					{
						path: 'sla',
						name: 'SlaPolicies',
						component: () => import('@/pages/desk/settings/sla/SlaPolicies.vue')
					},
					{
						path: 'sla/new',
						name: 'NewSlaPolicy',
						component: () => import('@/pages/desk/settings/sla/SlaPolicy.vue')
					},
					{
						path: 'sla/:slaId',
						name: 'SlaPolicy',
						component: () => import('@/pages/desk/settings/sla/SlaPolicy.vue'),
						props: true
					},
					{
						path: 'emails',
						name: 'Emails',
						component: () => import('@/pages/desk/settings/email/Emails.vue')
					},
					{
						path: 'emails/new',
						name: 'NewEmailAccount',
						component: () => import('@/pages/desk/settings/email/EmailAccount.vue')
					},
					{
						path: 'emails/:emailAccountId',
						name: 'EmailAccount',
						component: () => import('@/pages/desk/settings/email/EmailAccount.vue'),
						props: true
					},
					{
						path: 'helpdesk',
						name: 'Helpdesk Settings',
						component: () => import('@/pages/desk/settings/helpdesk/HelpdeskSettings.vue')
					}
				]
			}
		]
	},
	{
		path: '/support',
		name: 'Portal',
		component: () => import('@/pages/portal/Portal.vue'),
		children: [
			{
				path: 'tickets',
				name: 'ProtalTickets',
				component: () => import('@/pages/portal/Tickets.vue'),
			},
			{
				path: 'tickets/:ticketId',
				name: 'PortalTicket',
				component: () => import('@/pages/portal/Ticket.vue'),
				props: true
			},
			{
				path: 'tickets/new/:templateId',
				name: 'TemplatedNewTicket',
				component: () => import('@/pages/portal/NewTicket.vue'),
				props: true
			},
			{
				path: 'tickets/new',
				name: 'DefaultNewTicket',
				component: () => import('@/pages/portal/NewTicket.vue'),
			},
			{
				path: 'impersonate',
				name: 'Impersonate',
				component: () => import('@/pages/portal/Impersonate.vue')
			}
		]
	},
]

let router = createRouter({
	history: createWebHistory('/'),
	routes,
})

export default router
