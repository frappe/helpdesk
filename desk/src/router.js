import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/helpdesk/login',
		name: 'Login',
		component: () => import('@/pages/Login.vue'),
	},
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
				props: true,
				meta: {
					breadcrumbs(route) {
						return [
							{
								label: 'Tickets',
								path: '/helpdesk/tickets'
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
								path: '/helpdesk/contacts'
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
							return { path: '/helpdesk/settings/agents'}
						},
					},
					{
						path: 'agents',
						name: 'Agents',
						component: () => import('@/pages/desk/settings/agent/Agents.vue'),
						meta: {
							// breadcrumbs() {
							// 	return [
							// 		{
							// 			label: 'Settings',
							// 			path: '/helpdesk/settings'
							// 		},
							// 		{
							// 			label: 'Agents'
							// 		}
							// 	]
							// }
						}
					},
					{
						path: 'sla',
						name: 'SlaPolicies',
						component: () => import('@/pages/desk/settings/sla/SlaPolicies.vue'),
						meta: {
							// breadcrumbs() {
							// 	return [
							// 		{
							// 			label: 'Settings',
							// 			path: '/helpdesk/settings'
							// 		},
							// 		{
							// 			label: 'Support Policies'
							// 		}
							// 	]
							// }
						}
					},
					{
						path: 'sla/new',
						name: 'NewSlaPolicy',
						component: () => import('@/pages/desk/settings/sla/SlaPolicy.vue'),
						meta: {
							// breadcrumbs() {
							// 	return [
							// 		{
							// 			label: 'Settings',
							// 			path: '/helpdesk/settings'
							// 		},
							// 		{
							// 			label: 'Support Policies',
							// 			path: '/helpdesk/settings/sla'
							// 		},
							// 		{
							// 			label: 'New Support Policy'
							// 		}
							// 	]
							// }
						}
					},
					{
						path: 'sla/:slaId',
						name: 'SlaPolicy',
						component: () => import('@/pages/desk/settings/sla/SlaPolicy.vue'),
						props: true,
						meta: {
							// breadcrumbs(route) {
							// 	return [
							// 		{
							// 			label: 'Settings',
							// 			path: '/helpdesk/settings'
							// 		},
							// 		{
							// 			label: 'Support Policies',
							// 			path: '/helpdesk/settings/sla'
							// 		},
							// 		{
							// 			label: route.params.slaId
							// 		}
							// 	]
							// }
						}
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
