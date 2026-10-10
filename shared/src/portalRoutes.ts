import { CUSTOMER_PORTAL_ROOT, slugify } from './utils'

// Block JSONs repeat these paths.
export const ROUTES = {
  home: '/',
  categories: '/categories',
  // Search results mark matches in the title, which are not part of the slug.
  article: ({ name, title }: { name: string; title?: string }) =>
    `/articles/${[name, slugify(title?.replace(/<[^>]*>/g, ''))].filter(Boolean).join('-')}`,
  category: (name: string) => `/category/${name}`,
  ticketList: '/customer-tickets',
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
