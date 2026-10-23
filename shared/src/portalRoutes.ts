import { CUSTOMER_PORTAL_ROOT } from './utils'

// Block JSONs repeat these paths.
export const ROUTES = {
  ticketList: '/customer-tickets',
  newTicket: '/tickets/new',
  ticket: (name: string) => `/tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}
