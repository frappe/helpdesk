import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/ticket',
    name: 'Tickets',
    component: () => import('@/pages/Tickets.vue'),
  }
]

let router = createRouter({
  history: createWebHistory('/helpdesk'),
  routes,
})

export default router
