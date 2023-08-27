import { getPage } from "./utils";

export const CustomerPages = {
  path: "/my-tickets",
  component: () => getPage("CLayout"),
  meta: {
    auth: true,
  },
  children: [
    {
      path: "",
      name: "TicketsCustomer",
      component: () => getPage("TicketsCustomer"),
    },
    {
      path: "new/:templateId?",
      name: "TicketNew",
      component: () => getPage("TicketNew"),
      props: true,
      meta: {
        onSuccessRoute: "TicketCustomer",
        parent: "TicketsCustomer",
      },
    },
    {
      path: ":ticketId",
      name: "TicketCustomer",
      component: () => getPage("TicketCustomer"),
      props: true,
    },
  ],
};
