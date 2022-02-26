import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/helpdesk',
		name: 'Desk',
		component: () => import('@/pages/desk/Desk.vue'),
		children: [
			{
				path: 'tickets',
				name: 'Tickets',
				component: () => import('@/pages/desk/Tickets.vue'),
			},
			{
				path: 'tickets/:ticketId',
				name: 'Ticket',
				component: () => import('@/pages/desk/Ticket.vue'),
				props: true
			},
			{
				path: 'contacts',
				name: 'Contacts',
				component: () => import('@/pages/desk/Contacts.vue')
			},
			{
				path: 'settings',
				name: 'Settings',
				component: () => import('@/pages/desk/settings/Settings.vue'),
				children: [
					{
						path: 'agents',
						name: 'AgentSettings',
						component: () => import('@/pages/desk/settings/agent_settings/AgentSettings.vue')
					},
					{
						path: 'sla',
						name: 'SlaSettings',
						component: () => import('@/pages/desk/settings/sla_policy_settings/SlaPolicySettings.vue')
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
				path: '',
				redirect: () => {
					return { path: '/support/tickets'}
				},
			},
			{
				path: 'tickets',
				name: 'PortalTickets',
				component: () => import('@/pages/portal/Tickets.vue'),
			},
			{
				path: 'tickets/:ticketId',
				name: 'PortalTicket',
				component: () => import('@/pages/portal/Ticket.vue'),
				props: true
			},
		]
	},
]

let router = createRouter({
	history: createWebHistory('/'),
	routes,
})

export default router
