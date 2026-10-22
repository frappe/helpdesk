import { CUSTOMER_PORTAL_ROOT } from './utils'

// Block JSONs repeat these paths.
export const ROUTES = {
  home: '/',
  categories: '/categories',
  // Lists link the bare name; the article page adds the slug.
  article: ({ name, title_slug }: { name: string; title_slug?: string }) =>
    `/articles/${[name, title_slug].filter(Boolean).join('-')}`,
  category: (name: string) => `/category/${name}`,
  ticketList: '/my-tickets',
  newTicket: (origin?: TicketOrigin) => ({ path: '/my-tickets/new', query: originQuery(origin) }),
  ticket: (name: string) => `/my-tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}

// Stored as the ticket's entry point.
export type TicketOrigin =
  | { from: 'article'; article: string }
  | { from: 'search'; q?: string }
  | { from: 'ticket-list' | 'closed-ticket' }

// Drop empty values, so no bare `q=`.
function originQuery(origin?: TicketOrigin) {
  return Object.fromEntries(Object.entries(origin ?? {}).filter(([, value]) => value))
}
