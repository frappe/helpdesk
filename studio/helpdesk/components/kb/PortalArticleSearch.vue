<template>
  <Combobox
    v-model:open="isOpen"
    v-model:query="query"
    class="w-full !border-outline-gray-1 shadow-[0_1px_2px_rgba(0,0,0,0.05)] hover:!border-outline-gray-3 focus-within:!border-outline-gray-4 focus-within:!outline-1 data-[state=open]:!outline-1"
    trigger="input"
    variant="outline"
    size="lg"
    :placeholder="placeholder"
    :options="options"
    :loading="results.loading && !results.data"
    :filterable="false"
    :open-on-click="false"
    :offset="8"
    @focus="isOpen = hasHistory"
  >
    <template #prefix>
      <!-- On the axis of a result's thumbnail: the trigger's own padding lands it 9px short. -->
      <LucideSearch class="ml-[9px] size-4 text-ink-gray-4" />
    </template>
    <template #suffix><span /></template>

    <template #group-label="{ group }">
      <span class="flex min-w-0 flex-1 items-center">
        {{ group.group }}
      </span>
    </template>
    <template #item="{ item }">
      <div
        v-if="item.recentSearch"
        class="recent-search flex min-w-0 flex-1 items-center gap-3"
      >
        <LucideClock class="size-4 shrink-0 text-ink-gray-4" />
        <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
          {{ item.recentSearch }}
        </span>
        <button
          type="button"
          class="history-remove flex size-8 shrink-0 items-center justify-center rounded-[6px] text-ink-gray-4 hover:bg-surface-gray-3 hover:text-ink-gray-7"
          :aria-label="__('Remove')"
          @pointerdown.stop.prevent
          @click.stop.prevent="forgetSearch(item.recentSearch)"
        >
          <LucideX class="size-4" />
        </button>
      </div>
      <div
        v-else-if="item.recentArticle"
        class="recent-article flex min-w-0 flex-1 items-center gap-3"
      >
        <PortalArticleThumbnail
          class="[&:is(img)]:border [&:is(img)]:border-outline-gray-2"
          :src="item.recentArticle.image"
        />
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span class="min-w-0 truncate text-base text-ink-gray-8">
            {{ item.recentArticle.title }}
          </span>
          <span class="truncate text-p-sm text-ink-gray-5">
            {{ articleMeta(item.recentArticle) }}
          </span>
        </div>
        <button
          type="button"
          class="history-remove flex size-8 shrink-0 items-center justify-center rounded-[6px] text-ink-gray-4 hover:bg-surface-gray-3 hover:text-ink-gray-7"
          :aria-label="__('Remove')"
          @pointerdown.stop.prevent
          @click.stop.prevent="forgetArticle(item.recentArticle.name)"
        >
          <LucideX class="size-4" />
        </button>
      </div>
      <div
        v-else-if="item.key === SEARCH_ALL"
        class="flex min-w-0 items-center gap-3"
      >
        <span
          class="flex size-9 shrink-0 items-center justify-center rounded-5 bg-surface-gray-2 text-ink-gray-6"
        >
          <LucideSearch class="size-4" />
        </span>
        <span class="min-w-0 truncate text-base text-ink-gray-8">
          {{ __("Search for “{0}”", [searchText]) }}
        </span>
      </div>
      <div
        v-else
        class="flex min-w-0 items-start gap-3 [&_mark]:bg-transparent [&_mark]:font-semibold [&_mark]:text-ink-gray-9"
      >
        <PortalArticleThumbnail
          class="mt-px [&:is(img)]:border [&:is(img)]:border-outline-gray-2"
          :src="item.article.image"
        />
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span
            class="min-w-0 truncate text-base text-ink-gray-8"
            v-html="item.article.title"
          />
          <span
            class="line-clamp-1 text-p-sm text-ink-gray-5"
            v-html="item.article.excerpt"
          />
        </div>
      </div>
    </template>
  </Combobox>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Combobox } from "frappe-ui";
import LucideClock from "~icons/lucide/clock";
import LucideSearch from "~icons/lucide/search";
import LucideX from "~icons/lucide/x";
import { __ } from "@helpdesk/shared/translation";
import PortalArticleThumbnail from "@app/components/kb/PortalArticleThumbnail.vue";
import { ROUTES } from "@app/routes";
import { useArticleSearch } from "@app/composables/useArticleSearch";
import { useRecent, type RecentArticle } from "@app/stores/recent";

const MAX_RESULTS = 5;
const SEARCH_ALL = "search-all";
const RECENT_SEARCHES = "recent-searches";

withDefaults(defineProps<{ placeholder?: string }>(), {
  placeholder: "",
});

const router = useRouter();
const query = ref("");
const isOpen = ref(false);
const {
  recentSearches,
  recentArticles,
  rememberSearch,
  forgetSearch,
  forgetArticle,
} = useRecent();

const hasHistory = computed(
  () => recentSearches.value.length + recentArticles.value.length > 0
);

const results = useArticleSearch(query, { limit: MAX_RESULTS, minLength: 1 });

// Ours, not the slot's `query`: that stays empty when a recent search filled the box.
const searchText = computed(() => query.value.trim());
const isTyping = computed(() => searchText.value.length > 0);

watch(query, () => (isOpen.value = isTyping.value || hasHistory.value));

// Emptied from inside the open list, it closes rather than show nothing.
watch(hasHistory, (value) => {
  if (!value && !isTyping.value) isOpen.value = false;
});

function openArticle(name: string) {
  rememberSearch(query.value);
  router.push(ROUTES.article(name));
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
        onClick: () => router.push(ROUTES.article(article.name)),
      })),
    },
  ].filter((group) => group.options.length)
);

const resultOptions = computed(() => [
  ...(results.data || []).map((article) => ({
    type: "custom",
    key: article.name,
    label: article.title,
    article,
    onClick: () => openArticle(article.name),
  })),
  {
    type: "custom",
    key: SEARCH_ALL,
    label: __("Search"),
    onClick: () => {
      rememberSearch(searchText.value);
      router.push({ path: ROUTES.help, query: { q: searchText.value } });
    },
  },
]);

const options = computed(() =>
  isTyping.value ? resultOptions.value : historyOptions.value
);
</script>

<style>
/* Portaled to <body>, so unscoped; the large outline variant is this box's alone. */
[data-slot="content"][data-variant="outline"][data-size="lg"] {
  width: var(--reka-combobox-trigger-width);
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="content-body"]
  > div {
  /* Whatever room the popper has, so results under a phone's keyboard still scroll into reach. */
  max-height: calc(
    var(--reka-combobox-content-available-height, 100dvh) - 16px
  );
  overflow-y: auto;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="content-body"]
  > div {
  padding: 8px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"] {
  border-radius: 8px;
  padding: 0.75rem 0.5rem;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"]:not(:last-child) {
  border-bottom: 1px solid var(--outline-gray-1);
}
/* History, on an 8px grid: 40px search rows, 56px article rows, icons on the labels' edge. */
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="group-label"] {
  height: auto;
  padding: 8px 8px 4px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"]:has(.recent-search, .recent-article) {
  display: flex;
  align-items: center;
  border-bottom: 0;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"]:has(.recent-search) {
  height: 40px;
  padding: 0 4px 0 8px;
}
[data-slot="content"][data-variant="outline"][data-size="lg"]
  [data-slot="item"]:has(.recent-article) {
  min-height: 56px;
  padding: 0 4px 0 8px;
}
/* Only on the hovered row: the list highlights its first row on open. Touch has no hover, so it stays. */
.history-remove {
  opacity: 0;
}
[data-slot="item"]:hover .history-remove,
.history-remove:focus-visible {
  opacity: 1;
}
@media (pointer: coarse) {
  .history-remove {
    opacity: 1;
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
