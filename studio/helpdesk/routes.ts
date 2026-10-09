import { CUSTOMER_PORTAL_ROOT } from '@helpdesk/shared/utils'

// Block JSONs repeat these paths; a single-segment one also needs a hooks.py route rule.
export const ROUTES = {
  home: '/',
  categories: '/categories',
  article: ({ name, title }: { name: string; title?: string }) =>
    `/articles/${[name, slugify(title)].filter(Boolean).join('-')}`,
  category: (name: string) => `/category/${name}`,
  ticketList: '/customer-tickets',
  newTicket: '/tickets/new',
  ticket: (name: string) => `/tickets/${name}`,
  appRoot: CUSTOMER_PORTAL_ROOT,
}

function slugify(text = '') {
  return text
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .normalize('NFC')
    .toLowerCase()
    .replace(/[^\p{L}\p{M}\p{N}]+/gu, '-')
    .replace(/^-|-$/g, '')
}
