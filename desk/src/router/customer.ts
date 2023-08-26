import { getPage } from "./utils";

export const CustomerPages = {
  path: "/my-tickets",
  component: () => getPage("CLayout"),
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
    },
    {
      path: ":ticketId",
      name: "TicketCustomer",
      component: () => getPage("TicketCustomer"),
      props: true,
    },
  ],
};
