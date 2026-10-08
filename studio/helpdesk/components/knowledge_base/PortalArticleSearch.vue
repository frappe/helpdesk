<template>
  <Combobox
    ref="combobox"
    v-model:open="isOpen"
    v-model:query="query"
    class="w-full !border-outline-gray-1 shadow-[0_1px_2px_rgba(0,0,0,0.05)] hover:!border-outline-gray-3 focus-within:!border-outline-gray-4 focus-within:!outline-1 data-[state=open]:!outline-1"
    trigger="input"
    variant="outline"
    size="lg"
    :placeholder="placeholder"
    :options="options"
    :loading="isSearching"
    :filterable="false"
    :open-on-click="false"
    :offset="8"
    @focus="onFocus"
    @blur="isFocused = false"
  >
    <template #prefix>
      <!-- On the axis of a result's thumbnail: the trigger's own padding lands it 9px short. -->
      <LucideSearch class="ml-[9px] size-4 text-ink-gray-4" />
    </template>
    <template #suffix>
      <LoadingIndicator v-if="results.loading" class="size-4 text-ink-gray-4" />
      <KeyboardShortcut
        v-else-if="!query && !isFocused"
        class="slash-hint"
        combo="Slash"
        bg
      />
      <span v-else />
    </template>

    <template #group-label="{ group }">
      <span class="flex min-w-0 flex-1 items-center justify-between">
        {{ group.group }}
        <button
          v-if="group.key === RECENT_SEARCHES"
          type="button"
          class="text-sm text-ink-gray-5 hover:text-ink-gray-7"
          @pointerdown.prevent
          @click="clearSearches"
        >
          {{ __("Clear") }}
        </button>
      </span>
    </template>
    <template #item="{ item }">
      <div
        class="flex min-w-0 flex-1 items-center gap-3"
        :class="{ 'recent-search': item.recentSearch }"
      >
        <span
          v-if="item.recentSearch"
          class="flex w-9 shrink-0 justify-center text-ink-gray-4"
        >
          <LucideClock class="size-4" />
        </span>
        <span
          v-else
          class="article-tile flex size-9 shrink-0 items-center justify-center rounded-[8px] bg-surface-gray-2 text-ink-gray-6"
        >
          <LucideFileText class="size-4" />
        </span>

        <span
          v-if="item.recentSearch"
          class="min-w-0 flex-1 truncate text-base text-ink-gray-8"
        >
          {{ item.recentSearch }}
        </span>
        <div
          v-else
          class="flex min-w-0 flex-1 flex-col gap-0.5 [&_mark]:bg-transparent [&_mark]:font-semibold [&_mark]:text-ink-gray-9"
        >
          <span
            v-if="item.article"
            class="truncate text-base text-ink-gray-8"
            v-html="item.article.title"
          />
          <span v-else class="truncate text-base text-ink-gray-8">
            {{ item.recentArticle.title }}
          </span>
          <span v-if="item.article" class="truncate text-p-sm text-ink-gray-5">
            <template v-if="item.article.category_name">
              {{ item.article.category_name }} ·
            </template>
            <span v-html="item.article.excerpt" />
          </span>
          <span v-else class="truncate text-p-sm text-ink-gray-5">
            {{ articleMeta(item.recentArticle) }}
          </span>
        </div>

        <span class="flex size-8 shrink-0 items-center justify-center">
          <button
            v-if="item.onRemove"
            type="button"
            class="history-remove size-6 items-center justify-center rounded-[6px] text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-7"
            :aria-label="__('Remove')"
            @pointerdown.stop.prevent
            @click.stop.prevent="item.onRemove"
          >
            <LucideX class="size-3.5" />
          </button>
          <KeyboardShortcut class="row-enter" combo="Enter" bg />
        </span>
      </div>
    </template>

    <template #empty>
      <div class="flex flex-col items-center gap-1 px-4 py-8 text-center">
        <LucideSearchX class="mb-1 size-5 text-ink-gray-4" />
        <span class="max-w-full truncate text-base font-medium text-ink-gray-8">
          {{ __("No articles match “{0}”", [searchText]) }}
        </span>
        <span class="text-p-sm text-ink-gray-5">
          {{ __("Try other words, or ask our team.") }}
        </span>
        <Button
          class="mt-2"
          variant="solid"
          theme="gray"
          size="sm"
          icon-left="lucide-plus"
          :label="__('Create a ticket')"
          @pointerdown.prevent
          @click="createTicket"
        />
      </div>
    </template>

    <template v-if="!isEmpty" #footer>
      <div
        class="flex h-11 items-center justify-between gap-3 border-t border-outline-gray-1 px-3 text-sm text-ink-gray-5"
        @pointerdown.prevent
      >
        <div class="search-hints flex items-center gap-4">
          <span
            v-for="hint in KEY_HINTS"
            :key="hint.label"
            class="flex items-center gap-1.5"
          >
            <span class="flex gap-1">
              <kbd
                v-for="key in hint.keys"
                :key="key"
                class="flex h-5 min-w-5 items-center justify-center rounded-[5px] border border-outline-gray-2 bg-surface-base px-1 pt-px text-xs text-ink-gray-5"
              >
                {{ key }}
              </kbd>
            </span>
            {{ hint.label }}
          </span>
        </div>
        <div class="search-ticket flex items-center gap-2">
          {{ __("Can’t find it?") }}
          <Button
            variant="ghost"
            size="sm"
            icon-left="lucide-plus"
            :label="__('Create a ticket')"
            @click="createTicket"
          />
        </div>
      </div>
    </template>
  </Combobox>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  Button,
  Combobox,
  KeyboardShortcut,
  LoadingIndicator,
  useKeyboardShortcut,
} from "frappe-ui";
import LucideClock from "~icons/lucide/clock";
import LucideFileText from "~icons/lucide/file-text";
import LucideSearch from "~icons/lucide/search";
import LucideSearchX from "~icons/lucide/search-x";
import LucideX from "~icons/lucide/x";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@app/routes";
import { useArticleSearch } from "@app/composables/useArticleSearch";
import { useRecent, type RecentArticle } from "@app/stores/recent";

const MAX_RESULTS = 6;
const RECENT_SEARCHES = "recent-searches";
const KEY_HINTS = [
  { keys: ["↑", "↓"], label: __("Navigate") },
  { keys: ["↵"], label: __("Open") },
  { keys: ["esc"], label: __("Close") },
];

withDefaults(defineProps<{ placeholder?: string }>(), {
  placeholder: "",
});

const router = useRouter();
const combobox = ref<InstanceType<typeof Combobox> | null>(null);
const query = ref("");
const isOpen = ref(false);
const isFocused = ref(false);
const {
  recentSearches,
  recentArticles,
  rememberSearch,
  forgetSearch,
  clearSearches,
  forgetArticle,
} = useRecent();

const hasHistory = computed(
  () => recentSearches.value.length + recentArticles.value.length > 0
);

useKeyboardShortcut({
  combo: "Slash",
  description: __("Search articles"),
  handler: () => combobox.value?.focus(),
});

const results = useArticleSearch(query, { limit: MAX_RESULTS, minLength: 1 });

// Ours, not the slot's `query`: that stays empty when a recent search filled the box.
const searchText = computed(() => query.value.trim());
const isTyping = computed(() => searchText.value.length > 0);

watch(query, () => (isOpen.value = isTyping.value || hasHistory.value));

// Emptied from inside the open list, it closes rather than show nothing.
watch(hasHistory, (value) => {
  if (!value && !isTyping.value) isOpen.value = false;
});

function onFocus() {
  isFocused.value = true;
  isOpen.value = hasHistory.value;
}

function openArticle(article: { name: string; title: string }) {
  rememberSearch(query.value);
  router.push(ROUTES.article(article));
}

function createTicket() {
  const subject = searchText.value;
  router.push({ path: ROUTES.newTicket, query: subject ? { subject } : {} });
}

function articleMeta(article: RecentArticle) {
  const parts = [article.categoryName];
  if (article.minutes) parts.push(__("{0} min read", [article.minutes]));
  return parts.filter(Boolean).join(" · ");
}

const historyOptions = computed(() =>
  [
    {
      key: RECENT_SEARCHES,
      group: __("Recent searches"),
      options: recentSearches.value.map((text) => ({
        type: "custom",
        key: `search:${text}`,
        label: text,
        recentSearch: text,
        keepOpen: true,
        onClick: () => (query.value = text),
        onRemove: () => forgetSearch(text),
      })),
    },
    {
      key: "recently-viewed",
      group: __("Recently viewed"),
      options: recentArticles.value.map((article) => ({
        type: "custom",
        key: `article:${article.name}`,
        label: article.title,
        recentArticle: article,
        onClick: () => router.push(ROUTES.article(article)),
        onRemove: () => forgetArticle(article.name),
      })),
    },
  ].filter((group) => group.options.length)
);

// `params` changes when a fetch starts, so this is false from the keystroke until its answer lands.
const isCurrent = computed(
  () => !results.loading && results.params?.query?.trim() === searchText.value
);
const hasResults = computed(() => Boolean(results.data?.length));
const isSearching = computed(
  () => isTyping.value && !isCurrent.value && !hasResults.value
);
const isEmpty = computed(
  () => isTyping.value && isCurrent.value && !hasResults.value
);

const resultOptions = computed(() =>
  (results.data || []).map((article) => ({
    type: "custom",
    key: article.name,
    label: article.title,
    article,
    // The previous query's rows stay in view, but Enter must not open one.
    disabled: !isCurrent.value,
    onClick: () => openArticle(article),
  }))
);

const options = computed(() =>
  isTyping.value ? resultOptions.value : historyOptions.value
);
</script>

<style>
/* Portaled to <body>, so unscoped; the large outline variant is this box's alone. */
[data-slot="content"][data-variant="outline"][data-size="lg"] {
  width: var(--reka-combobox-trigger-width);
}
/* Whatever room the popper has, so results under a phone's keyboard still scroll into reach. */
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="content-body"] {
  display: flex;
  flex-direction: column;
  max-height: calc(
    var(--reka-combobox-content-available-height, 100dvh) - 16px
  );
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="content-body"]
  > div:not([data-slot="footer"]) {
  min-height: 0;
  max-height: none;
  overflow-y: auto;
  padding: 8px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="footer"] {
  flex-shrink: 0;
}
/* On an 8px grid: 40px search rows, 52px article rows, icons on the labels' edge. */
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="group-label"] {
  height: auto;
  padding: 8px 8px 4px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"] {
  display: flex;
  align-items: center;
  min-height: 52px;
  height: auto;
  padding: 8px;
  border-radius: 8px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"]:has(.recent-search) {
  min-height: 40px;
  height: 40px;
  padding: 0 8px;
}
[data-slot="item"][data-highlighted] .article-tile {
  background-color: var(--surface-gray-3);
}
/* The list highlights its first row on open, so ↵ marks Enter's target; a hovered history row offers X instead. */
.history-remove,
.row-enter {
  display: none;
}
[data-slot="item"]:hover .history-remove {
  display: flex;
}
@media (pointer: fine) {
  [data-slot="item"][data-highlighted] .row-enter {
    display: inline-flex;
  }
  [data-slot="item"]:hover .history-remove + .row-enter {
    display: none;
  }
}
/* Touch has no hover or keys: X always shows, key hints never do. */
@media (pointer: coarse) {
  .history-remove {
    display: flex;
  }
  .slash-hint {
    display: none;
  }
}
@media (max-width: 639px), (pointer: coarse) {
  .search-hints {
    display: none;
  }
  .search-ticket {
    flex: 1;
    justify-content: space-between;
  }
}
/* The rule between the sections runs edge to edge, through the panel's padding. */
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="group"]
  + [data-slot="group"] {
  margin: 8px -8px 0;
  padding: 8px 8px 0;
  border-top: 1px solid var(--outline-elevation-2);
}
</style>
