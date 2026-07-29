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

export const breadcrumb = computed(() => stack.value.map((level) => level.title));
export const depth = computed(() => stack.value.length);

/**
 * Every command here is an agent command — nav, settings, availability, ticket
 * search. AppSidebar is shared with the customer portal, so the gate lives with
 * the state rather than on the mount site, which has two parents.
 */
export const isPaletteAvailable = computed(() => !isCustomerPortal.value);

// --- context -------------------------------------------------------------

const contextDismissed = ref(false);

/**
 * The ticket you have open, or null off a ticket page and once the chip is
 * dismissed. Derived from the route so it can never go stale behind a
 * navigation the palette didn't cause.
 */
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
  // Route every open through here, Cmd+K included, or the open rate undercounts
  // the only path most agents use.
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

// Guards run() against a second Enter landing mid-await: without it a
// double-Enter stacked a duplicate level, or double-toggled a tag.
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
  // `runs ÷ opens` below 0.5 means agents open, miss and press Esc; a long
  // query or a non-zero depth on a common action means the ranking is wrong.
  capture("command_palette_command_run", {
    data: {
      command_id: command.id,
      query_length: query.value.length,
      depth: depth.value,
    },
  });
  if (command.keepOpen) {
    // Optimistic: the tick flips on Enter, and flips back if the write fails.
    // Waiting for the round trip left the row looking like it ignored the key.
    flipChecked(command);
    running = true;
    try {
      await command.perform?.();
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

/**
 * Visible rows for the current level, grouped. Group order follows the best
 * score inside it, so once the user types, nav links sink below real matches.
 */
export const groups = computed<PaletteGroup[]>(() => {
  // Without this the root list rebuilds on every route change, forever, even
  // for users who never press Cmd+K.
  if (!isOpen.value) return [];

  const level = stack.value.at(-1);
  if (level) {
    // A single group's header only repeats the breadcrumb ("Change priority"
    // over "Set priority"); multi-group levels like Settings keep theirs.
    const grouped = groupCommands(level.commands, query.value);
    return grouped.length === 1
      ? grouped.map((group) => ({ ...group, title: "" }))
      : grouped;
  }

  // Untitled: the chip already says what these rows act on, so a "Ticket"
  // header would only repeat it.
  const scoped = context.value
    ? groupCommands(ticketCommands(context.value.id), query.value).map(
        (group) => ({ ...group, title: "" })
      )
    : [];

  const term = query.value.trim();
  // An empty query with the chip up leads with the ticket's rows, then recents
  // — jumping to another recent ticket is the highest-frequency zero-typing
  // action, and the ticket page is exactly where it happens from. Without the
  // chip (removed, or a context-free page) the empty query must fall through
  // to the global root, not an empty list.
  if (!term && context.value)
    return [...scoped, ...groupCommands(recentTicketCommands(), "")];
  if (!term) return groupCommands(globalCommands(), "");

  // Scope *ranks*, it never *gates*. Returning early here is what made a ticket
  // whose subject contains "open" unreachable: `Set status: Open` matched, and
  // global search never ran. Scoped rows already win on CONTEXT_WEIGHT, so
  // appending costs nothing but keeps search reachable.
  return [...scoped, ...groupCommands(globalCommands(), term), ...fallback(term)];
});

/**
 * Pinned, not last-resort. `fuzzyScore` matches subsequences, so almost any real
 * word matches *something* — an only-when-nothing-matched fallback stays hidden
 * exactly when it is needed. Matters most because `title_only: true` searches
 * subjects only, so a phrase from an email body finds nothing here.
 */
function fallback(term: string): PaletteGroup[] {
  if (term.length < MIN_QUERY_LENGTH) return [];
  // Untitled: "Search all of Helpdesk for X" explains itself, a heading above
  // it was one more thing to read.
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
    // ponytail: a missing FTS index or server error yields no rows; the
    // "Search all of Helpdesk" fallback still routes the user somewhere.
    // Add a `subject like` fallback if unindexed sites become common.
    if (token === latestSearchToken) searchResults.value = [];
  } finally {
    if (token === latestSearchToken) searchLoading.value = false;
  }
}, 200);

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
  // Deliberately keeping the old rows until the new ones land. Clearing here
  // blanked the list on every keystroke and resized the panel under the cursor,
  // 200ms of debounce at a time.
  searchLoading.value = true;
  debouncedSearch(trimmed, latestSearchToken);
}

/** Drops the current results *and* any response still in flight. */
export function clearSearch(): void {
  latestSearchToken += 1;
  searchResults.value = [];
  searchLoading.value = false;
}
