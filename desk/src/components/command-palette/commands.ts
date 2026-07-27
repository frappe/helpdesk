import { agentPortalSidebarOptions } from "@/components/layouts/layoutSettings";
import {
  setActiveSettingsTab,
  showSettingsModal,
  tabs as settingsTabs,
} from "@/components/Settings/settingsModal";
import { router } from "@/router";
import { useAgentStatusStore } from "@/stores/agentStatus";
import { useAuthStore } from "@/stores/auth";
import { useTelephonyStore } from "@/stores/telephony";
import { __ } from "@/translation";
import { useTheme } from "frappe-ui";
import { FALLBACK_GROUP, GROUP, type Command } from "./paletteTypes";
import { recentCommandIds, recentTickets } from "./recentTickets";
import { ticketCommands } from "./ticketCommands";
import { ticketListCommands } from "./ticketListCommands";

import LucideActivity from "~icons/lucide/activity";
import LucideClock from "~icons/lucide/clock";
import LucideFileSearch from "~icons/lucide/file-search";
import LucideLogOut from "~icons/lucide/log-out";
import LucideMoon from "~icons/lucide/moon";
import LucidePlus from "~icons/lucide/plus";
import LucideSettings from "~icons/lucide/settings";
import LucideSun from "~icons/lucide/sun";
import LucideTicket from "~icons/lucide/ticket";

/**
 * The whole palette in source order. Context first: on a ticket, that ticket's
 * actions outrank everything else, which is the behaviour that separates a
 * palette from a search box.
 */
export function buildRootCommands(query: string): Command[] {
  const route = router.currentRoute.value;
  const ticketId =
    route.name === "TicketAgent" ? String(route.params.ticketId) : "";
  const always = [
    ...navigateCommands(),
    ...createCommands(),
    ...accountCommands(),
  ];
  return [
    ...ticketJumpCommand(query),
    ...(ticketId ? ticketCommands(ticketId) : []),
    ...(route.name === "TicketsAgent" ? ticketListCommands() : []),
    ...(query ? [] : recentCommands(always)),
    ...always,
  ];
}

/** "#234" jumps straight to that ticket — the one prefix the palette already taught. */
function ticketJumpCommand(query: string): Command[] {
  const match = query.trim().match(/^#?(\d+)$/);
  if (!match) return [];
  const ticketId = match[1];
  return [
    {
      id: `jump-${ticketId}`,
      title: __("Go to ticket #{0}", [ticketId]),
      group: GROUP.navigate,
      icon: LucideTicket,
      rank: 2000, // an explicit id beats any fuzzy match
      perform: () => router.push({ name: "TicketAgent", params: { ticketId } }),
    },
  ];
}

// --- recents -------------------------------------------------------------

/** Clones of rows in `always`, so recents can't drift from the real commands. */
function recentCommands(always: Command[]): Command[] {
  return [...recentlyRunCommands(always), ...recentTicketCommands()];
}

function recentlyRunCommands(always: Command[]): Command[] {
  return recentCommandIds.value
    .map((id) => always.find((command) => command.id === id))
    .filter((command): command is Command => Boolean(command))
    .map((command) => ({ ...command, group: GROUP.recent, weight: 1 }));
}

function recentTicketCommands(): Command[] {
  return recentTickets.value.map((ticket) => ({
    id: `recent-ticket-${ticket.name}`,
    title: ticket.subject,
    subtitle: `#${ticket.name}`,
    group: GROUP.recent,
    icon: LucideClock,
    perform: () =>
      router.push({ name: "TicketAgent", params: { ticketId: ticket.name } }),
  }));
}

// --- navigation, create, account -----------------------------------------

/** The sidebar's own nav list, so labels and icons can't drift from it. */
function navigateCommands(): Command[] {
  const callingEnabled = useTelephonyStore().isCallingEnabled;
  return agentPortalSidebarOptions
    .filter((option) => callingEnabled || option.label !== __("Call Logs"))
    .map((option) => ({
      id: `go-${option.to}`,
      title: __(option.label),
      group: GROUP.navigate,
      icon: option.icon,
      weight: 0.7, // nav links are noise once the user has typed something real
      perform: () => router.push({ name: option.to }),
    }));
}

function createCommands(): Command[] {
  return [
    {
      id: "new-ticket",
      title: __("New ticket"),
      group: GROUP.create,
      icon: LucidePlus,
      keywords: "create raise add",
      perform: () => router.push({ name: "TicketAgentNew" }),
    },
    {
      id: "new-article",
      title: __("New article"),
      group: GROUP.create,
      icon: LucidePlus,
      keywords: "create knowledge base kb",
      perform: () =>
        router.push({ name: "NewArticle", params: { id: "new" } }),
    },
  ];
}

function accountCommands(): Command[] {
  const { toggleTheme, currentTheme } = useTheme();
  return [
    {
      id: "toggle-theme",
      title: __("Toggle theme"),
      group: GROUP.account,
      icon: currentTheme.value === "dark" ? LucideSun : LucideMoon,
      keywords: "dark light appearance",
      perform: () => toggleTheme(),
    },
    {
      id: "availability",
      title: __("Set availability"),
      group: GROUP.account,
      icon: LucideActivity,
      keywords: "status away online offline",
      children: () => availabilityChildren(),
    },
    {
      id: "settings",
      title: __("Settings"),
      group: GROUP.account,
      icon: LucideSettings,
      hint: "Mod+,",
      keywords: "preferences configure email agents teams sla telephony",
      children: () => settingsChildren(),
    },
    {
      id: "logout",
      title: __("Log out"),
      group: GROUP.account,
      icon: LucideLogOut,
      keywords: "sign out exit",
      perform: () => useAuthStore().logout(),
    },
  ];
}

/**
 * Every settings tab as its own row, so "sla" jumps straight to SLA Policies.
 * Derived from the settings `tabs` computed, which is already permission
 * filtered — no second copy of who-can-see-what to keep in sync.
 */
function settingsChildren(): Command[] {
  return settingsTabs.value.flatMap((section) =>
    section.items.map((item) => ({
      id: `settings-${item.label}`,
      title: item.label,
      // Keep the settings modal's own section headers as palette groups.
      group: section.label,
      // Profile's icon is a prebuilt Avatar VNode, which `:is` can't render.
      icon: isVNode(item.icon) ? LucideSettings : item.icon,
      perform: () => openSettingsTab(item.label),
    }))
  );
}

function isVNode(value: unknown): boolean {
  return Boolean(value && (value as { __v_isVNode?: boolean }).__v_isVNode);
}

function openSettingsTab(label: string): void {
  setActiveSettingsTab(label as Parameters<typeof setActiveSettingsTab>[0]);
  showSettingsModal.value = true;
}

function availabilityChildren(): Command[] {
  const store = useAgentStatusStore();
  return (store.statusOptions ?? []).map((status: string) => ({
    id: `availability-${status}`,
    title: __(status),
    group: "Set availability",
    icon: LucideActivity,
    perform: () => store.setMyStatus(status),
  }));
}

/**
 * Shown only when nothing matched, so the palette is never a dead end —
 * the typed text is carried into whatever the user picks.
 */
export function buildFallbackCommands(query: string): Command[] {
  return [
    {
      id: "fallback-search",
      title: __('Search all of Helpdesk for "{0}"', [query]),
      group: FALLBACK_GROUP,
      icon: LucideFileSearch,
      perform: () => router.push({ name: "SearchAgent", query: { q: query } }),
    },
    {
      id: "fallback-create",
      title: __('Create ticket "{0}"', [query]),
      group: FALLBACK_GROUP,
      icon: LucidePlus,
      perform: () =>
        router.push({ name: "TicketAgentNew", query: { subject: query } }),
    },
  ];
}

