<template>
  <Combobox
    v-model:open="isOpen"
    v-model:query="query"
    class="w-full"
    trigger="input"
    variant="subtle"
    size="lg"
    :placeholder="placeholder"
    :options="options"
    :loading="results.loading"
    :filterable="false"
    :open-on-click="false"
  >
    <template #prefix>
      <!-- On the axis of a result's thumbnail: the trigger's own padding lands it 9px short. -->
      <LucideSearch class="ml-[9px] size-4 text-ink-gray-4" />
    </template>
    <template #suffix><span /></template>

    <template #item="{ item, query }">
      <div
        v-if="item.key === SEARCH_ALL"
        class="flex min-w-0 items-center gap-3"
      >
        <span
          class="flex size-9 shrink-0 items-center justify-center rounded-5 bg-surface-gray-2 text-ink-gray-6"
        >
          <LucideSearch class="size-4" />
        </span>
        <span class="min-w-0 truncate text-base leading-[1.15] text-ink-gray-8">
          {{ __("Search for “{0}”", [query.trim()]) }}
        </span>
      </div>
      <div
        v-else
        class="flex min-w-0 items-start gap-3 [&_mark]:bg-transparent [&_mark]:font-semibold [&_mark]:text-ink-gray-9"
      >
        <PortalArticleThumbnail class="mt-px" :src="item.article.image" />
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span
            class="min-w-0 truncate text-base leading-[1.15] text-ink-gray-8"
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
// Header search: the server matches, the Combobox lists and drives the keyboard.
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Combobox, createResource, debounce } from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import { __ } from "@helpdesk/shared/translation";
import PortalArticleThumbnail from "@app/components/kb/PortalArticleThumbnail.vue";
import { ROUTES } from "@app/routes";

const MAX_RESULTS = 5;
const SEARCH_ALL = "search-all";
const SEARCH_DEBOUNCE_MS = 300;

withDefaults(defineProps<{ placeholder?: string }>(), {
  placeholder: "",
});

const router = useRouter();
const query = ref("");
// Query-driven: an empty box has nothing to open over.
const isOpen = ref(false);

const results = createResource({
  url: "helpdesk.api.knowledge_base.search_articles",
  method: "GET",
  makeParams: () => ({ query: query.value, limit: MAX_RESULTS }),
});

const search = debounce(() => results.fetch(), SEARCH_DEBOUNCE_MS);

watch(query, (value) => {
  isOpen.value = value.trim().length > 0;
  if (isOpen.value) search();
});

const options = computed(() => [
  ...(results.data || []).map((article) => ({
    type: "custom",
    key: article.name,
    label: article.title,
    article,
    onClick: () => router.push(ROUTES.article(article.name)),
  })),
  {
    type: "custom",
    key: SEARCH_ALL,
    label: __("Search"),
    // Always offered, so a search that matched nothing here still has somewhere to go.
    onClick: ({ query }) =>
      router.push({ path: ROUTES.help, query: { q: query.trim() } }),
  },
]);
</script>

<style>
/* Portaled to <body>, so unscoped; the large subtle variant is this box's alone. */
[data-slot="content"][data-variant="subtle"][data-size="lg"] {
  width: var(--reka-combobox-trigger-width);
}
[data-slot="content"][data-variant="subtle"][data-size="lg"]
  [data-slot="content-body"]
  > div {
  max-height: none;
}
[data-slot="content"][data-variant="subtle"][data-size="lg"]
  [data-slot="item"] {
  border-radius: 6px;
  padding: 0.75rem 0.5rem;
}
[data-slot="content"][data-variant="subtle"][data-size="lg"]
  [data-slot="item"]:not(:last-child) {
  border-bottom: 1px solid var(--outline-gray-1);
}
</style>
