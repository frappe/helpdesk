<template>
  <Combobox
    ref="combobox"
    v-model:open="isOpen"
    v-model:query="query"
    class="min-h-[42px] w-full !gap-1.5 !rounded-6 !border-outline-gray-2 !px-3.5 shadow-lg hover:!border-outline-gray-3 focus-within:!border-outline-gray-4 focus-within:!outline-0 data-[state=open]:!border-outline-gray-4 data-[state=open]:!outline-0 [&_input]:!text-base"
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
      <LucideSearch class="size-4.5 text-ink-gray-5" />
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

    <template #item="{ item }">
      <div class="flex min-w-0 flex-1 items-start gap-3">
        <PortalArticleIcon class="mt-0.5 size-4 shrink-0 text-ink-gray-4" />
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <span
            v-if="item.article"
            class="truncate text-base text-ink-gray-8 [&_mark]:rounded-[2px] [&_mark]:bg-surface-amber-2 [&_mark]:text-ink-gray-9"
            v-html="item.article.title"
          />
          <span v-else class="truncate text-base text-ink-gray-8">
            {{ item.recentArticle.title }}
          </span>
          <span
            v-if="item.article"
            class="truncate text-p-sm text-ink-gray-5 [&_mark]:bg-transparent [&_mark]:text-ink-gray-5"
          >
            <template v-if="item.article.category_name">
              {{ item.article.category_name }} ·
            </template>
            <span v-html="item.article.excerpt" />
          </span>
          <span v-else class="truncate text-p-sm text-ink-gray-5">
            {{
              articleMeta(
                item.recentArticle.categoryName,
                item.recentArticle.minutes
              )
            }}
          </span>
        </div>

        <span class="flex size-6 shrink-0 items-center justify-center self-center">
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
          <LucideCornerDownLeft class="row-enter size-4 text-ink-gray-5" />
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
          variant="subtle"
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
        class="flex h-11 items-center justify-between gap-3 border-t border-outline-gray-2 px-3 text-sm text-ink-gray-5"
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
import LucideCornerDownLeft from "~icons/lucide/corner-down-left";
import LucideSearch from "~icons/lucide/search";
import LucideSearchX from "~icons/lucide/search-x";
import LucideX from "~icons/lucide/x";
import { __ } from "@helpdesk/shared/translation";
import PortalArticleIcon from "@app/components/knowledge_base/PortalArticleIcon.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import {
  MIN_QUERY_LENGTH,
  useArticleSearch,
} from "@app/composables/useArticleSearch";
import { useRecent } from "@app/stores/recent";
import { articleMeta, countLabel } from "@app/utils";

const MAX_RESULTS = 6;
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
const { recentArticles, forgetArticle } = useRecent();

const hasHistory = computed(() => recentArticles.value.length > 0);

useKeyboardShortcut({
  combo: "Slash",
  description: __("Search articles"),
  handler: () => combobox.value?.focus(),
});

const results = useArticleSearch(query, { limit: MAX_RESULTS });

const searchText = computed(() => query.value.trim());
const canSearch = computed(
  () => searchText.value.length >= MIN_QUERY_LENGTH
);

watch(query, () => (isOpen.value = canSearch.value || hasHistory.value));

// Emptied from inside the open list, it closes rather than show nothing.
watch(hasHistory, (value) => {
  if (!value && !canSearch.value) isOpen.value = false;
});

function onFocus() {
  isFocused.value = true;
  isOpen.value = hasHistory.value;
}

function createTicket() {
  router.push(ROUTES.newTicket({ from: "search", q: searchText.value }));
}

const historyOptions = computed(() =>
  hasHistory.value
    ? [
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
      ]
    : []
);

// `params` changes when a fetch starts, so this is false from the keystroke until its answer lands.
const isCurrent = computed(
  () => !results.loading && results.params?.query?.trim() === searchText.value
);
const hasResults = computed(() => Boolean(results.data?.length));
const isSearching = computed(
  () => canSearch.value && !isCurrent.value && !hasResults.value
);
const isEmpty = computed(
  () => canSearch.value && isCurrent.value && !hasResults.value
);

const resultOptions = computed(() =>
  hasResults.value
    ? [
        {
          key: "results",
          group: countLabel(results.data.length, __("1 article"), __("{0} articles")),
          options: results.data.map((article) => ({
            type: "custom",
            key: article.name,
            label: article.title,
            article,
            // The previous query's rows stay in view, but Enter must not open one.
            disabled: !isCurrent.value,
            onClick: () => router.push(ROUTES.article(article)),
          })),
        },
      ]
    : []
);

const options = computed(() =>
  canSearch.value ? resultOptions.value : historyOptions.value
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
/* On an 8px grid: 52px article rows, icons on the labels' edge. */
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="group-label"] {
  height: auto;
  padding: 8px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"] {
  display: flex;
  align-items: flex-start;
  min-height: 52px;
  height: auto;
  padding: 8px;
  border-radius: 8px;
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
