import {
  agentPortalSidebarOptions,
  showShortcutsModal,
} from "@/components/layouts/layoutSettings";
import {
  setActiveSettingsTab,
  tabs as settingsTabs,
  showSettingsModal,
} from "@/components/Settings/settingsModal";
import { router } from "@/router";
import { useAgentStatusStore } from "@/stores/agentStatus";
import { useAuthStore } from "@/stores/auth";
import { useTelephonyStore } from "@/stores/telephony";
import { parseColor } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { useTheme } from "frappe-ui";
import { GROUP, type Command } from "./paletteTypes";
import { recentTickets } from "./recentTickets";
import { ticketListCommands } from "./ticketListCommands";

import LucideActivity from "~icons/lucide/activity";
import LucideClock from "~icons/lucide/clock";
import LucideFileSearch from "~icons/lucide/file-search";
import LucideKeyboard from "~icons/lucide/keyboard";
import LucideLogOut from "~icons/lucide/log-out";
import LucideMoon from "~icons/lucide/moon";
import LucidePlus from "~icons/lucide/plus";
import LucideSettings from "~icons/lucide/settings";
import LucideSun from "~icons/lucide/sun";
import LucideTicket from "~icons/lucide/ticket";

/** Extra root rows per route. Values stay lazy: they read page-published state. */
const routeCommands: Record<string, () => Command[]> = {
  TicketsAgent: ticketListCommands,
};

/** The global list. The open ticket's actions live in the context chip, not here. */
export function buildRootCommands(query: string): Command[] {
  const route = router.currentRoute.value;
  return [
    ...ticketJumpCommand(query),
    ...(routeCommands[String(route.name ?? "")]?.() ?? []),
    ...(query ? [] : recentTicketCommands()),
    ...navigateCommands(),
    ...createCommands(),
    ...accountCommands(),
  ];
}

/** "#234" jumps straight to that ticket — the one prefix the palette already taught. */
function ticketJumpCommand(query: string): Command[] {
  const ticketId = query.trim().match(/^#?(\d+)$/)?.[1];
  if (!ticketId) return [];
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
export function recentTicketCommands(): Command[] {
  const openTicketId = String(router.currentRoute.value.params.ticketId ?? "");
  return recentTickets.value
    .filter((ticket) => ticket.name !== openTicketId)
    .map((ticket) => ({
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
      perform: () => router.push({ name: "NewArticle", params: { id: "new" } }),
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
      // Live status names too, so site-defined values ("Lunch") match.
      keywords:
        "my status presence online offline away busy " +
        useAgentStatusStore().statusOptions.join(" "),
      children: () => availabilityChildren(),
    },
    {
      id: "settings",
      title: __("Settings"),
      group: GROUP.account,
      icon: LucideSettings,
      hint: "Mod+,",
      keywords: "preferences email agents teams sla telephony erpnext",
      children: () => settingsChildren(),
    },
    {
      id: "shortcuts",
      title: __("Keyboard shortcuts"),
      group: GROUP.account,
      icon: LucideKeyboard,
      hint: "Mod+/",
      keywords: "keys hotkeys bindings help",
      perform: () => (showShortcutsModal.value = true),
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

/** One row per settings tab, from the already permission-filtered `tabs` computed. */
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

async function availabilityChildren(): Promise<Command[]> {
  const store = useAgentStatusStore();
  // The level snapshots this result; a cold store would freeze it empty.
  await store.statuses.list.promise;
  return (store.statusOptions ?? []).map((status: string) => ({
    id: `availability-${status}`,
    title: __(status),
    group: "Set availability",
    dotClass: parseColor(store.getStatus(status)?.color ?? "Gray"),
    checked: status === store.myStatus,
    perform: () => store.setMyStatus(status),
  }));
}

/** Never a dead end: the typed text carries into whatever the user picks. */
export function buildFallbackCommands(query: string): Command[] {
  const commands: Command[] = [
    {
      id: "fallback-search",
      title: __('Search for "{0}"', [query]),
      titleSuffix: __("(advanced search)"),
      group: "",
      icon: LucideFileSearch,
      perform: () => router.push({ name: "SearchAgent", query: { q: query } }),
    },
  ];
  // "#123" is someone reaching for a ticket, not naming a new one.
  if (!query.startsWith("#")) {
    commands.push({
      id: "fallback-create",
      title: __('Create ticket "{0}"', [query]),
      group: "",
      icon: LucidePlus,
      perform: () =>
        router.push({ name: "TicketAgentNew", query: { subject: query } }),
    });
  }
  return commands;
}
