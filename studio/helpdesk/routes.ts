import { CUSTOMER_PORTAL_ROOT } from '@helpdesk/shared/utils'

// Block JSONs repeat these paths; a single-segment one also needs a hooks.py route rule.
export const ROUTES = {
  home: '/',
  help: '/help',
  categories: '/categories',
  article: (name: string) => `/articles/${name}`,
  category: (name: string) => `/category/${name}`,
  ticketList: '/customer-tickets',
  newTicket: '/tickets/new',
  ticket: (name: string) => `/tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}
