import { CUSTOMER_PORTAL_ROOT } from './utils'

// Block JSONs repeat these paths.
export const ROUTES = {
  home: '/',
  categories: '/categories',
  // Lists link the bare name; the article page then adds the slug `get_article` sends.
  article: ({ name, title_slug }: { name: string; title_slug?: string }) =>
    `/articles/${[name, title_slug].filter(Boolean).join('-')}`,
  category: (name: string) => `/category/${name}`,
  ticketList: '/my-tickets',
  newTicket: (origin?: TicketOrigin) => ({ path: '/tickets/new', query: originQuery(origin) }),
  ticket: (name: string) => `/tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}

// Where a "raise a ticket" link sits; the server stores it as the ticket's entry point.
export type TicketOrigin =
  | { from: 'article'; article: string }
  | { from: 'search'; q?: string }
  | { from: 'ticket-list' | 'closed-ticket' }

// Empty values stay out, so a search with no text does not leave a bare `q=` in the URL.
function originQuery(origin?: TicketOrigin) {
  return Object.fromEntries(Object.entries(origin ?? {}).filter(([, value]) => value))
}
