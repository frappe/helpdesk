import { CUSTOMER_PORTAL_ROOT } from '@helpdesk/shared/utils'

// Block JSONs carry path literals too, so a route that moves must change in both.
export const ROUTES = {
  ticketList: '/customer-tickets',
  ticket: (name: string) => `/tickets/${name}`,
  // Absolute, for navigations that leave the SPA (login redirects, logout).
  appRoot: CUSTOMER_PORTAL_ROOT,
}
