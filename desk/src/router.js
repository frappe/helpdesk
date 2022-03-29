import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/helpdesk',
		name: 'Desk',
		component: () => import('@/pages/desk/Desk.vue'),
		children: [
			{
				path: '',
				redirect: () => {
					return { path: '/helpdesk/tickets'}
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
				props: true
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
				props: true
			},
			{
				path: 'settings',
				name: 'Settings',
				component: () => import('@/pages/desk/settings/Settings.vue'),
				children: [
					{
						path: '',
						redirect: () => {
							return { path: '/helpdesk/settings/agents'}
						},
					},
					{
						path: 'agents',
						name: 'Agents',
						component: () => import('@/pages/desk/settings/agent/Agents.vue')
					},
					{
						path: 'sla',
						name: 'SlaPolicies',
						component: () => import('@/pages/desk/settings/sla/SlaPolicies.vue')
					},
					{
						path: 'sla/new',
						name: 'SlaPolicy',
						component: () => import('@/pages/desk/settings/sla/SlaPolicy.vue')
					},
					{
						path: 'sla/:slaId',
						name: 'SlaPolicy',
						component: () => import('@/pages/desk/settings/sla/SlaPolicy.vue'),
						props: true
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
			}
		]
	},
]

let router = createRouter({
	history: createWebHistory('/'),
	routes,
})

export default router
