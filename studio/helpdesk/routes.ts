// Block JSONs carry path literals too, so a route that moves must change in both.

export const ROUTES = {
  home: '/',
  ticketList: '/customer-tickets',
  newTicket: '/new-ticket',
  ticket: (name: string) => `/tickets/${name}`,
  // Absolute, for navigations that leave the SPA (login redirects, logout).
  appRoot: '/kb',
}
