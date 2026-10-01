import { CUSTOMER_PORTAL_ROOT } from '@helpdesk/shared/utils'

// Block JSONs carry path literals too, so a route that moves must change in both.
export const ROUTES = {
  home: '/',
  help: '/help',
  article: (name: string) => `/articles/${name}`,
  category: (name: string) => `/category/${name}`,
  ticketList: '/customer-tickets',
  newTicket: '/tickets/new',
  ticket: (name: string) => `/tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}
