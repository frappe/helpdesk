import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/ticket',
    name: 'Tickets',
    component: () => import('@/pages/Tickets.vue'),
  },
  {
    path: '/ticket/:ticketId',
    name: 'TicketConversation',
    component: () => import('@/pages/TicketConversation.vue'),
    props: true
  }
]

let router = createRouter({
  history: createWebHistory('/helpdesk'),
  routes,
})

export default router
