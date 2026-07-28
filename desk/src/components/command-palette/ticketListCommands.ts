import {
  applyListFilters,
  type FilterCondition,
} from "@/components/listViewFilters";
import { views } from "@/composables/useView";
import { router } from "@/router";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import type { View } from "@/types";
import { priorityOptions, statusOptions } from "./optionCommands";
import { CONTEXT_WEIGHT, GROUP, type Command } from "./paletteTypes";

import LucideCircleDot from "~icons/lucide/circle-dot";
import LucideFilterX from "~icons/lucide/filter-x";
import LucideFlag from "~icons/lucide/flag";
import LucideLayoutList from "~icons/lucide/layout-list";
import LucideUser from "~icons/lucide/user";

/**
 * Actions for the ticket list. Every one navigates — filters travel as a URL
 * query that ListViewBuilder merges over the active view, so the palette stays
 * decoupled from the list component (it can't `inject` the list's actions
 * anyway; the palette lives in the sidebar, outside that provide chain).
 *
 * Surfaced only on the list route. The routing mechanism would work from any
 * page, but showing list actions while reading a ticket buries the ticket's own.
 */
export function ticketListCommands(): Command[] {
  return [
    {
      id: "list-filter-status",
      title: __("Filter by status"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideCircleDot,
      // No `hint` here: the app's "f" opens the whole filter popover, which is
      // not what this row does. A hint that doesn't map 1:1 teaches the wrong key.
      keywords: "open replied resolved closed paused",
      children: () => statusFilterChildren(),
    },
    {
      id: "list-filter-priority",
      title: __("Filter by priority"),
      group: GROUP.list,
      weight: CONTEXT_WEIGHT,
      icon: LucideFlag,
      keywords: "urgent high medium low",
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
  const ticketViews = (views.data ?? []).filter(
    (view: View) => view.dt === "HD Ticket"
  );
  return [
    {
      id: "list-view-default",
      title: __("List"),
      group: "Switch view",
      icon: LucideLayoutList,
      perform: () => router.push({ name: "TicketsAgent" }),
    },
    ...ticketViews.map((view: View) => ({
      id: `list-view-${view.name}`,
      title: view.label ?? view.name,
      subtitle: viewScope(view),
      group: "Switch view",
      icon: LucideLayoutList,
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

/**
 * Layers onto the list's existing filters; an empty list clears them. Falls
 * back to the URL only when no list is mounted — the URL is a one-way write the
 * popover never reads back, so repeating a filter there is a dead key.
 */
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
