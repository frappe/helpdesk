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
  newTicket: (origin?: TicketOrigin) => ({ path: '/my-tickets/new', query: compactQuery(origin) }),
  ticket: (name: string) => `/my-tickets/${name}`,
  search: (query?: { q?: string; category?: string | string[] }) => ({ path: '/search', query: compactQuery(query) }),
  appRoot: CUSTOMER_PORTAL_ROOT,
}

// Stored as the ticket's entry point.
export type TicketOrigin =
  | { from: 'article'; article: string }
  | { from: 'search'; q?: string }
  | { from: 'ticket-list' | 'closed-ticket' }

// Drop empty values and lists, so no bare `q=`.
function compactQuery(query: object = {}) {
  return Object.fromEntries(Object.entries(query).filter(([, value]) => [value].flat().some(Boolean)))
}
