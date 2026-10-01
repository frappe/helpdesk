import LucideContact2 from "~icons/lucide/contact-2";
import LucideTicket from "~icons/lucide/ticket";
import LucideLayoutDashboard from "~icons/lucide/layout-dashboard";
import { OrganizationsIcon } from "../icons";
import LucideHome from "~icons/lucide/home";
import LucideFolderKanban from "~icons/lucide/folder-kanban";
import LucideListTodo from "~icons/lucide/list-todo";
import LucideClipboardList from "~icons/lucide/clipboard-list";
import LucideClock from "~icons/lucide/clock";
import LucideBarChartHorizontal from "~icons/lucide/bar-chart-horizontal";
import { __ } from "@/translation";

export const agentPortalSidebarOptions = [
  {
    label: __("Home"),
    icon: LucideHome,
    to: "Home",
  },
  {
    label: __("Dashboard"),
    icon: LucideLayoutDashboard,
    to: "Dashboard"
  },
  {
    label: __("Tickets"),
    icon: LucideTicket,
    to: "TicketsAgent",
  },
  {
    label: __("Projects"),
    icon: LucideFolderKanban,
    to: "TaskyProjects",
  },
  {
    label: __("Templates"),
    icon: LucideClipboardList,
    to: "TaskyTemplates",
  },
  {
    label: __("My Tasks"),
    icon: LucideListTodo,
    to: "TaskyMyTasks",
  },
  {
    label: __("Timesheets"),
    icon: LucideClock,
    to: "TaskyTimesheets",
  },
  {
    label: __("Task Status"),
    icon: LucideBarChartHorizontal,
    to: "TaskyStatusReport",
  },
  {
    label: __("Customers"),
    icon: OrganizationsIcon,
    to: "CustomerList",
  },
  {
    label: __("Contacts"),
    icon: LucideContact2,
    to: "ContactList",
  },
];

export const customerPortalSidebarOptions = [
  {
    label: __("Tickets"),
    icon: LucideTicket,
    to: "TicketsCustomer",
  },
];
