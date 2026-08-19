import { useTicket } from "@/composables/useTicket";
import { router } from "@/router";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { isCustomerPortal } from "@/utils";
import { useDebounceFn } from "@vueuse/core";
import { createResource, toast } from "frappe-ui";
import { computed, ref, shallowRef } from "vue";
import {
  buildFallbackCommands,
  buildRootCommands,
  recentTicketCommands,
} from "./commands";
import { scoreCommand } from "./fuzzyScore";
import {
  GROUP,
  type Command,
  type PaletteContext,
  type SearchItem,
} from "./paletteTypes";
import { searchCommands } from "./searchCommands";
import { ticketCommands } from "./ticketCommands";

// Module scope: the sidebar button, Cmd+K and the dialog drive one instance.
export const isOpen = ref(false);
export const query = ref("");

interface Level {
  title: string;
  commands: Command[];
}

export interface PaletteGroup {
  title: string;
  items: Command[];
}

const stack = shallowRef<Level[]>([]); // drill-down levels, empty = root
const loadingChildren = ref(false);

export const breadcrumb = computed(() =>
  stack.value.map((level) => level.title)
);
export const depth = computed(() => stack.value.length);

/** Agent-only; AppSidebar is shared with the customer portal, so the gate lives here. */
export const isPaletteAvailable = computed(() => !isCustomerPortal.value);

// --- context -------------------------------------------------------------

const contextDismissed = ref(false);

/** The open ticket, or null once dismissed. Route-derived so it can't go stale. */
export const context = computed<PaletteContext | null>(() => {
  if (contextDismissed.value) return null;
  const route = router.currentRoute.value;
  if (route.name !== "TicketAgent") return null;
  const id = String(route.params.ticketId);
  return {
    id,
    label: `#${id}`,
    title: useTicket(id).ticket.doc?.subject ?? "",
  };
});

/** Drops the chip and widens the list back out to every global command. */
export function dismissContext(): void {
  contextDismissed.value = true;
  query.value = "";
  clearSearch();
}

export function openPalette(): void {
  if (!isPaletteAvailable.value) return;
  isOpen.value = true;
  // Every open path routes through here, Cmd+K included, so the count is honest.
  capture("command_palette_opened", {
    data: { context: String(router.currentRoute.value.name ?? "") },
  });
}

export function closePalette(): void {
  isOpen.value = false;
}

export function resetPalette(): void {
  stack.value = [];
  query.value = "";
  contextDismissed.value = false;
  clearSearch();
}

/** Pops one drill-down level. Backspace on an empty query calls this. */
export function back(): void {
  if (!stack.value.length) return;
  stack.value = stack.value.slice(0, -1);
  query.value = "";
  clearSearch(); // else the pre-drill-down hits linger under an empty query
}

// A second Enter mid-await stacked a duplicate level or double-toggled a tag.
let running = false;

/** Drills in when the command has children, otherwise performs it and closes. */
export async function run(command: Command): Promise<void> {
  if (!command || running) return;
  if (command.children) {
    loadingChildren.value = true;
    running = true;
    try {
      const commands = await command.children();
      stack.value = [...stack.value, { title: command.title, commands }];
      query.value = "";
      clearSearch();
    } catch {
      toast.error(__("Could not load {0}", [command.title]));
    } finally {
      loadingChildren.value = false;
      running = false;
    }
    return;
  }
  capture("command_palette_command_run", {
    data: {
      command_id: command.id,
      query_length: query.value.length,
      depth: depth.value,
    },
  });
  if (command.keepOpen) {
    // Optimistic: waiting for the round trip made the row look like it ignored Enter.
    flipChecked(command);
    running = true;
    try {
      await command.perform?.();
      back(); // done toggling — return to the parent level
    } catch {
      flipChecked(command);
    } finally {
      running = false;
    }
    return;
  }
  closePalette();
  command.perform?.();
}

/** Flips a row's tick in the current level without rebuilding it. */
function flipChecked(target: Command): void {
  const level = stack.value.at(-1);
  if (!level) return;
  const commands = level.commands.map((command) =>
    command.id === target.id
      ? { ...command, checked: !command.checked }
      : command
  );
  stack.value = [...stack.value.slice(0, -1), { ...level, commands }];
}

// Frozen while closed: skips rebuilds for users who never open the palette, and
// keeps the rows on screen through the close fade instead of "No commands found".
let lastGroups: PaletteGroup[] = [];

/** Visible rows for the current level, grouped, ordered by best score inside. */
export const groups = computed<PaletteGroup[]>(() => {
  if (!isOpen.value) return lastGroups;
  return (lastGroups = buildGroups());
});

function buildGroups(): PaletteGroup[] {
  const level = stack.value.at(-1);
  if (level) {
    // A single group's header only repeats the breadcrumb; Settings keeps its many.
    const grouped = groupCommands(level.commands, query.value);
    return grouped.length === 1
      ? grouped.map((group) => ({ ...group, title: "" }))
      : grouped;
  }

  // The chip already says what "Ticket" rows act on; named sections keep headers.
  const scoped = context.value
    ? groupCommands(ticketCommands(context.value.id), query.value).map(
        (group) =>
          group.title === __(GROUP.ticket) ? { ...group, title: "" } : group
      )
    : [];

  const term = query.value.trim();
  // Chip + empty query: ticket rows then recents. No chip: the global root.
  if (!term && context.value)
    return [...scoped, ...groupCommands(recentTicketCommands(), "")];
  if (!term) return groupCommands(globalCommands(), "");

  // Scope *ranks*, never *gates*: returning scoped-only made a ticket whose
  // subject contains "open" unreachable behind "Set status: Open".
  return [
    ...scoped,
    ...groupCommands(globalCommands(), term),
    ...fallback(term),
  ];
}

/** Pinned, not last-resort: almost any word fuzzy-matches *something*, so an
 * only-when-empty fallback would hide exactly when needed. */
function fallback(term: string): PaletteGroup[] {
  if (term.length < MIN_QUERY_LENGTH) return [];
  return [{ title: "", items: buildFallbackCommands(term) }];
}

function globalCommands(): Command[] {
  return [
    ...buildRootCommands(query.value),
    ...searchCommands(searchResults.value),
  ];
}

function groupCommands(source: Command[], term: string): PaletteGroup[] {
  const typed = Boolean(term.trim());
  const matched = source
    .filter((command) => typed || !command.hideWhenEmpty)
    .map((command, index) => ({
      command,
      score: scoreCommand(command, term),
      index,
    }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score || a.index - b.index);

  const byGroup = new Map<string, Command[]>();
  for (const { command } of matched) {
    if (!byGroup.has(command.group)) byGroup.set(command.group, []);
    byGroup.get(command.group)!.push(command);
  }
  return [...byGroup].map(([title, items]) => ({ title: __(title), items }));
}

export const flatItems = computed(() => groups.value.flatMap((g) => g.items));
export const isLoading = computed(
  () => loadingChildren.value || searchLoading.value
);

// --- ticket search -------------------------------------------------------

export const searchResults = shallowRef<SearchItem[]>([]);
const searchLoading = ref(false);
let latestSearchToken = 0;

const MIN_QUERY_LENGTH = 2;
const SEARCH_RESULT_LIMIT = 6;

const searchResource = createResource({ url: "helpdesk.api.search.search" });

const debouncedSearch = useDebounceFn(async (term: string, token: number) => {
  try {
    const response = await searchResource.submit({
      query: term,
      title_only: true,
    });
    if (token !== latestSearchToken) return; // a newer keystroke won
    searchResults.value = (response?.results ?? []).slice(
      0,
      SEARCH_RESULT_LIMIT
    );
  } catch {
    if (token === latestSearchToken) searchResults.value = [];
  } finally {
    if (token === latestSearchToken) searchLoading.value = false;
  }
}, 300);

/** Token advances on every change, so a response can't land under a newer query. */
export function onQueryChange(term: string): void {
  query.value = term;
  latestSearchToken += 1;
  const trimmed = term.trim();
  if (stack.value.length || trimmed.length < MIN_QUERY_LENGTH) {
    searchResults.value = [];
    searchLoading.value = false;
    return;
  }
  // Old rows stay until new ones land; clearing here blanked the list per keystroke.
  searchLoading.value = true;
  debouncedSearch(trimmed, latestSearchToken);
}

/** Drops the current results *and* any response still in flight. */
export function clearSearch(): void {
  latestSearchToken += 1;
  searchResults.value = [];
  searchLoading.value = false;
}
