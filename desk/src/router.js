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
	}
]

let router = createRouter({
	history: createWebHistory('/helpdesk'),
	routes,
})

export default router
