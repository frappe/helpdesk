import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/',
		redirect: () => {
			return { path: '/tickets' }
		},
	},
	{
		path: '/tickets',
		name: 'Tickets',
		component: () => import('@/pages/Tickets.vue'),
	},
	{
		path: '/tickets/:ticketId',
		name: 'Ticket',
		component: () => import('@/pages/Ticket.vue'),
		props: true
	},
	{
		path: '/contacts',
		name: 'Contacts',
		component: () => import('@/pages/Contacts.vue')
	},
	{
		path: '/settings',
		name: 'Settings',
		component: () => import('@/pages/settings/Settings.vue'),
		children: [
			{
				path: 'agents',
				name: 'AgentSettings',
				component: () => import('@/pages/settings/agent_settings/AgentSettings.vue')
			},
			{
				path: 'sla',
				name: 'SlaSettings',
				component: () => import('@/pages/settings/sla_policy_settings/SlaPolicySettings.vue')
			}
		]
	}
]

let router = createRouter({
	history: createWebHistory('/helpdesk'),
	routes,
})

export default router
