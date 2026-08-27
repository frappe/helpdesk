import {
  applyListFilters,
  type FilterCondition,
} from "@/components/listViewFilters";
import { views } from "@/composables/useView";
import { router } from "@/router";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import type { View } from "@/types";
import { getIcon } from "@/utils";
import {
  priorityKeywords,
  priorityOptions,
  statusKeywords,
  statusOptions,
} from "./optionCommands";
import { CONTEXT_WEIGHT, GROUP, type Command } from "./paletteTypes";

import LucideCircleDot from "~icons/lucide/circle-dot";
import LucideFilterX from "~icons/lucide/filter-x";
import LucideFlag from "~icons/lucide/flag";
import LucideLayoutList from "~icons/lucide/layout-list";
import LucideUser from "~icons/lucide/user";

/** List-route actions. Filters travel as a URL query — the palette lives in the
 * sidebar, outside the list's provide chain, so it cannot inject its actions. */
export function ticketListCommands(): Command[] {
  return [
    {
      id: "list-filter-status",
      title: __("Filter by status"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideCircleDot,
      // No "f" hint: that key opens the whole filter popover, not this row.
      keywords: statusKeywords(),
      children: () => statusFilterChildren(),
    },
    {
      id: "list-filter-priority",
      title: __("Filter by priority"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideFlag,
      keywords: priorityKeywords(),
      children: () => priorityFilterChildren(),
    },
    {
      id: "list-assigned-to-me",
      title: __("Show tickets assigned to me"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideUser,
      keywords: "mine my assignment",
      perform: () =>
        applyFilter([["_assign", "like", `%${useAuthStore().userId}%`]]),
    },
    {
      id: "list-switch-view",
      title: __("Switch view"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideLayoutList,
      keywords: "saved public private preset",
      children: () => viewChildren(),
    },
    {
      id: "list-clear-filters",
      title: __("Clear filters"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideFilterX,
      keywords: "reset remove all",
      perform: () => applyFilter([]),
    },
  ];
}

function statusFilterChildren(): Command[] {
  return statusOptions({
    group: "Filter by status",
    onPick: (status) => applyFilter([["status", "=", status]]),
  });
}

function priorityFilterChildren(): Command[] {
  return priorityOptions({
    group: "Filter by priority",
    onPick: (priority) => applyFilter([["priority", "=", priority]]),
  });
}

function viewChildren(): Command[] {
  // The active view travels in the route query; absent means the default list.
  const currentView = String(router.currentRoute.value.query.view ?? "");
  const ticketViews = (views.data ?? []).filter(
    (view: View) => view.dt === "HD Ticket"
  );
  return [
    {
      id: "list-view-default",
      title: __("List"),
      group: "Switch view",
      icon: LucideLayoutList,
      checked: !currentView,
      perform: () => router.push({ name: "TicketsAgent" }),
    },
    ...ticketViews.map((view: View) => ({
      id: `list-view-${view.name}`,
      title: view.label ?? view.name,
      subtitle: viewScope(view),
      group: "Switch view",
      // Same resolver as the sidebar: emoji, lucide name, or the ticket default.
      icon: () => getIcon(view.icon),
      checked: view.name === currentView,
      perform: () =>
        router.push({ name: "TicketsAgent", query: { view: view.name } }),
    })),
  ];
}

function viewScope(view: View): string {
  if (view.public) return __("Public");
  if (view.pinned) return __("Pinned");
  return __("Private");
}

/** Layers onto the list's filters; empty clears. URL fallback only when no list
 * is mounted — the popover never reads the URL back. */
function applyFilter(conditions: FilterCondition[]): void {
  if (applyListFilters(conditions)) return;
  router.push({
    name: "TicketsAgent",
    query: {
      ...currentViewQuery(),
      filters: JSON.stringify(conditions),
    },
  });
}

/** Keep the active view when filtering, so filters layer onto it. */
function currentViewQuery(): Record<string, string> {
  const view = router.currentRoute.value.query.view;
  return view ? { view: String(view) } : {};
}
