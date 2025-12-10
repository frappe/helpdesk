import LucideBookOpen from "~icons/lucide/book-open";
import LucideContact2 from "~icons/lucide/contact-2";
import LucideTicket from "~icons/lucide/ticket";
import PhoneIcon from "../icons/PhoneIcon.vue";

export const agentPortalSidebarOptions = [
  {
    label: "Tickets",
    icon: LucideTicket,
    to: "TicketsAgent",
  },
  {
    label: "Contacts",
    icon: LucideContact2,
    to: "ContactList",
  },
  {
    label: "Call Logs",
    icon: PhoneIcon,
    to: "CallLogs",
  },
];

export const customerPortalSidebarOptions = [
  {
    label: "Tickets",
    icon: LucideTicket,
    to: "TicketsCustomer",
  },
  {
    label: "Knowledge Base",
    icon: LucideBookOpen,
    to: "CustomerKnowledgeBase",
  },
];
