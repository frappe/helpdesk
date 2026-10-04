import { CUSTOMER_PORTAL_ROOT } from '@helpdesk/shared/utils'

// Block JSONs repeat these paths; a single-segment one also needs a hooks.py route rule.
export const ROUTES = {
  ticketList: '/customer-tickets',
  ticket: (name: string) => `/tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}
