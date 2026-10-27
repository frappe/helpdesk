<template>
  <div class="flex flex-col pb-20">
    <!-- Sticky search and filters; bled into the column padding so rows scroll under it. -->
    <div
      class="sticky top-0 z-10 -mx-3 bg-surface-base px-3 pt-5 sm:-mx-5 sm:px-5 sm:pt-6"
    >
      <TextInput
        ref="input"
        v-model="query"
        :placeholder="__('Search articles')"
        :aria-label="__('Search articles')"
      >
        <template #prefix>
          <span class="lucide-search w-4 text-ink-gray-5" aria-hidden="true" />
        </template>
        <template v-if="query" #suffix>
          <button
            type="button"
            class="grid size-6 place-content-center rounded-4 p-1 focus-visible:focus-ring"
            :aria-label="__('Clear search')"
            @click="clear"
          >
            <span class="lucide-x w-4 text-ink-gray-7" aria-hidden="true" />
          </button>
        </template>
      </TextInput>

      <div v-if="canSearch" class="flex flex-wrap items-center gap-2 pt-2">
        <MultiSelect v-model="selected" hide-search :options="options">
          <template #trigger>
            <Button
              variant="outline"
              icon-left="lucide-list-filter"
              :label="filterLabel"
            />
          </template>
          <template #item-suffix="{ item }">
            <span class="text-xs tabular-nums text-ink-gray-5">{{
              item.count
            }}</span>
          </template>
        </MultiSelect>
        <Button
          v-for="chip in chips"
          :key="chip.name"
          variant="subtle"
          icon-right="lucide-x"
          :aria-label="__('Remove filter {0}', [chip.label])"
          @click="remove(chip.name)"
        >
          <!-- A slot, not `label`: Button lets `label` override aria-label. -->
          {{ chip.label }}
        </Button>
      </div>
      <!-- Rows fade into the toolbar as they scroll under it. -->
      <div
        class="pointer-events-none absolute inset-x-0 top-full h-6 bg-gradient-to-b from-surface-base/90 to-transparent"
      />
    </div>

    <p
      v-if="summary"
      class="mt-2 flex min-h-6 items-center text-sm text-ink-gray-6"
    >
      {{ summary }}
    </p>

    <PortalSkeleton
      v-if="canSearch && !search.rows.length && !search.isCurrent"
      class="mt-5"
      variant="category-rows"
      :count="5"
    />
    <div v-else-if="rows.length" class="mt-5 flex flex-col">
      <div
        class="-mx-2.5 transition-opacity"
        :class="{ 'opacity-50': canSearch && !search.isCurrent }"
      >
        <PortalLink
          v-for="row in rows"
          :key="row.name"
          :to="ROUTES.article(row)"
          class="group relative flex flex-col rounded-4 px-2.5 py-3 transition-colors hover:bg-surface-gray-1 focus-visible:focus-ring after:absolute after:inset-x-2.5 after:bottom-0 after:h-px after:bg-[--outline-gray-1] last:after:hidden hover:after:opacity-0 [&:has(+*:hover)]:after:opacity-0"
          @mouseenter="prefetchOnHover(row.name)"
        >
          <div class="flex min-w-0 items-center">
            <span
              v-if="canSearch"
              class="truncate text-base font-medium text-ink-gray-9"
              :class="MARK"
              v-html="row.title"
            />
            <span v-else class="truncate text-base font-medium text-ink-gray-9">
              {{ row.title }}
            </span>
            <span
              v-if="row.category"
              class="shrink-0 truncate px-1 text-sm leading-none text-ink-gray-5 max-sm:hidden"
            >
              &middot; {{ row.category }}
            </span>
            <span class="ms-auto shrink-0 ps-3 text-sm text-ink-gray-5">
              {{ articleMeta(undefined, row.minutes) }}
            </span>
          </div>
          <p
            v-if="row.excerpt"
            class="mt-1 line-clamp-2 text-p-base text-ink-gray-6"
            :class="MARK"
            v-html="row.excerpt"
          />
        </PortalLink>
      </div>
      <Button
        v-if="canSearch && search.hasMore"
        class="mx-auto mt-4"
        :label="__('Load more')"
        :loading="search.isLoading && search.isCurrent"
        @click="search.loadMore"
      />
    </div>
    <div
      v-else-if="canSearch"
      class="flex flex-col items-center gap-1 py-16 text-center"
    >
      <span
        class="lucide-search-x mb-1 size-5 text-ink-gray-4"
        aria-hidden="true"
      />
      <span class="max-w-full truncate text-base font-medium text-ink-gray-8">
        {{ __("No articles match “{0}”", [searchText]) }}
      </span>
      <span class="text-p-sm text-ink-gray-5">
        {{ __("Try other words, or ask our team.") }}
      </span>
      <Button
        class="mt-2"
        variant="solid"
        icon-left="lucide-plus"
        :label="__('Raise a ticket')"
        @click="
          router.push(ROUTES.newTicket({ from: 'search', q: searchText }))
        "
      />
    </div>
    <div v-else class="flex flex-col items-center gap-3 py-16 text-center">
      <div
        class="flex size-12 items-center justify-center rounded-full bg-surface-gray-2"
      >
        <span class="lucide-search size-6 text-ink-gray-5" aria-hidden="true" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <span class="text-base text-ink-gray-7">{{
          __("Type to search articles")
        }}</span>
        <span class="text-sm text-ink-gray-5">{{
          __("Use at least 3 characters.")
        }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Button, MultiSelect, TextInput, useKeyboardShortcut } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { articleMeta, countLabel } from "@helpdesk/shared/utils";
import {
  MIN_QUERY_LENGTH,
  usePagedArticleSearch,
} from "@app/composables/useArticleSearch";
import { prefetchOnHover, useKnowledgeBase } from "@app/stores/knowledgeBase";
import { useRecent } from "@app/stores/recent";
import PortalLink from "@app/components/ui/PortalLink.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";

const route = useRoute();
const router = useRouter();
const { sidebar } = useKnowledgeBase();
const { recentArticles } = useRecent();

const query = ref(String(route.query.q || ""));
const selected = ref<string[]>(
  [route.query.category].flat().filter(Boolean).map(String),
);
const search = usePagedArticleSearch(query, selected);

const input = ref<InstanceType<typeof TextInput> | null>(null);
onMounted(() => input.value?.focus());
useKeyboardShortcut({
  combo: "Slash",
  description: __("Search articles"),
  handler: () => input.value?.focus(),
});

watch([query, selected], () =>
  router.replace(ROUTES.search({ q: query.value, category: selected.value })),
);

const searchText = computed(() => query.value.trim());
const canSearch = computed(() => searchText.value.length >= MIN_QUERY_LENGTH);

// Drop URL names this reader cannot see. A known Category with no matches
// for the current query stays: it still scopes the search.
const checked = ref(false);
watch(
  () => sidebar.data,
  (rows) => {
    if (checked.value || !rows) return;
    checked.value = true;
    selected.value = selected.value.filter((name) =>
      rows.some((row) => row.name === name),
    );
  },
  { immediate: true },
);

const labelOf = (name: string) =>
  sidebar.data?.find((row) => row.name === name)?.label || name;

// As the server's `category_label_sort_key`: General first, then by label
// parts, so a Subcategory follows its parent. The sidebar sorts by name only.
function byLabel(a: { label: string }, b: { label: string }) {
  const [left, right] = [a.label, b.label].map((label) =>
    label.split(" › ").map((part) => part.toLocaleLowerCase()),
  );
  const general =
    Number(left[0] !== "general") - Number(right[0] !== "general");
  if (general) return general;
  for (let index = 0; index < Math.min(left.length, right.length); index++) {
    if (left[index] !== right[index])
      return left[index] < right[index] ? -1 : 1;
  }
  return left.length - right.length;
}

// Selected rows stay listed so they can be unchecked.
const options = computed(() =>
  (sidebar.data || [])
    .filter(
      (row) => row.name in search.counts || selected.value.includes(row.name),
    )
    .map((row) => ({
      value: row.name,
      label: row.label,
      count: search.counts[row.name] || 0,
    }))
    .sort(byLabel),
);
const chips = computed(() =>
  checked.value
    ? selected.value.map((name) => ({ name, label: labelOf(name) }))
    : [],
);
const filterLabel = computed(() =>
  selected.value.length
    ? __("Category · {0}", [selected.value.length])
    : __("Category"),
);

// The API escapes everything except <mark>, so v-html is safe on search rows.
const MARK =
  "[&_mark]:rounded-sm [&_mark]:bg-surface-amber-2 [&_mark]:px-0.5 [&_mark]:text-ink-gray-9";

const rows = computed(() =>
  canSearch.value
    ? search.rows.map((row) => ({ ...row, category: row.category_label }))
    : recentArticles.value.map((row) => ({
        ...row,
        category: row.categoryName,
      })),
);
const summary = computed(() => {
  if (!canSearch.value) return rows.value.length ? __("Recently viewed") : "";
  if (!search.isCurrent && !search.rows.length) return "";
  return countLabel(search.total, __("1 article"), __("{0} articles"));
});

function clear() {
  query.value = "";
  input.value?.focus();
}

function remove(name: string) {
  selected.value = selected.value.filter((value) => value !== name);
}
</script>
