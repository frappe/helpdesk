// The portal's routes, named once. Block JSONs still carry path literals — JSON
// cannot import — so a route that moves must change here and in the blocks that
// name it (grep the studio_page JSONs for the old path).

export const ROUTES = {
  home: '/',
  ticketList: '/customer-tickets',
  newTicket: '/new-ticket',
  ticket: (name: string) => `/tickets/${name}`,
  /** Absolute, for full-page navigations that leave the SPA (login redirects, logout). */
  appRoot: '/kb',
}
