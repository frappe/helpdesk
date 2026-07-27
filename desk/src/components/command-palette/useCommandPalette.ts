import { __ } from "@/translation";
import { useDebounceFn } from "@vueuse/core";
import { createResource, toast } from "frappe-ui";
import { computed, ref, shallowRef } from "vue";
import { buildFallbackCommands, buildRootCommands } from "./commands";
import { fuzzyScore } from "./fuzzyScore";
import { FALLBACK_GROUP, type Command, type SearchItem } from "./paletteTypes";
import { searchCommands } from "./searchCommands";
import { trackRecentCommand } from "./recentTickets";

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

const stack = shallowRef<Level[]>([]);
const loadingChildren = ref(false);

export const breadcrumb = computed(() => stack.value.map((level) => level.title));
export const depth = computed(() => stack.value.length);

export function openPalette(): void {
  isOpen.value = true;
}

export function closePalette(): void {
  isOpen.value = false;
}

export function resetPalette(): void {
  stack.value = [];
  query.value = "";
  clearSearch();
}

/** Pops one drill-down level. Backspace on an empty query calls this. */
export function back(): void {
  if (!stack.value.length) return;
  stack.value = stack.value.slice(0, -1);
  query.value = "";
  clearSearch(); // else the pre-drill-down hits linger under an empty query
}

/** Drills in when the command has children, otherwise performs it and closes. */
export async function run(command: Command): Promise<void> {
  if (!command) return;
  if (command.children) {
    loadingChildren.value = true;
    try {
      const commands = await command.children();
      stack.value = [...stack.value, { title: command.title, commands }];
      query.value = "";
      clearSearch();
    } catch {
      toast.error(__("Could not load {0}", [command.title]));
    } finally {
      loadingChildren.value = false;
    }
    return;
  }
  trackRecentCommand(command.id);
  closePalette();
  command.perform?.();
}

function scoreCommand(command: Command, term: string): number {
  if (command.rank !== undefined) return command.rank;
  if (!term) return 0;
  const base = Math.max(
    fuzzyScore(command.title, term),
    command.keywords ? fuzzyScore(command.keywords, term) - 50 : -1,
    command.subtitle ? fuzzyScore(command.subtitle, term) - 100 : -1
  );
  if (base < 0) return -1;
  return base * (command.weight ?? 1);
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
  const source = level
    ? level.commands
    : [
        ...buildRootCommands(query.value),
        ...searchCommands(searchResults.value),
      ];

  const matched = source
    .map((command, index) => ({
      command,
      score: scoreCommand(command, query.value),
      index,
    }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score || a.index - b.index);

  const byGroup = new Map<string, Command[]>();
  for (const { command } of matched) {
    if (!byGroup.has(command.group)) byGroup.set(command.group, []);
    byGroup.get(command.group)!.push(command);
  }
  const built = [...byGroup].map(([title, items]) => ({
    title: __(title),
    items,
  }));

  // Never a dead end: carry the typed text into something useful.
  if (!built.length && query.value.trim() && !level) {
    const fallbacks = buildFallbackCommands(query.value.trim());
    return [{ title: __(FALLBACK_GROUP), items: fallbacks }];
  }
  return built;
});

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
  clearSearch();
  const trimmed = term.trim();
  if (stack.value.length || trimmed.length < MIN_QUERY_LENGTH) return;
  searchLoading.value = true;
  debouncedSearch(trimmed, latestSearchToken);
}

/** Drops the current results *and* any response still in flight. */
export function clearSearch(): void {
  latestSearchToken += 1;
  searchResults.value = [];
  searchLoading.value = false;
}
