import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
  }
]

let router = createRouter({
  history: createWebHistory('/helpdesk'),
  routes,
})

export default router
