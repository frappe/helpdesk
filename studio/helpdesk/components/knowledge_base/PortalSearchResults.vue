<template>
  <div class="flex flex-col">
    <div class="sticky top-0 z-10 bg-surface-base pb-3 pt-3">
      <TextInput
        ref="input"
        v-model="query"
        size="lg"
        variant="outline"
        class="[&_input]:font-semibold"
        :placeholder="__('Search articles')"
        :aria-label="__('Search articles')"
      >
        <template #prefix>
          <span
            class="lucide-search size-4 text-ink-gray-4"
            aria-hidden="true"
          />
        </template>
        <template v-if="query" #suffix>
          <Button
            variant="ghost"
            size="xs"
            icon="lucide-x"
            :aria-label="__('Clear search')"
            @click="clear"
          />
        </template>
      </TextInput>

      <div v-if="canSearch" class="mt-3 flex flex-wrap items-center gap-2">
        <MultiSelect v-model="selected" hide-search :options="options">
          <template #trigger>
            <Button
              size="sm"
              icon-left="lucide-list-filter"
              :label="filterLabel"
            />
          </template>
          <template #item-suffix="{ item }">
            <span class="text-sm tabular-nums text-ink-gray-5">{{
              item.count
            }}</span>
          </template>
        </MultiSelect>
        <Button
          v-for="chip in chips"
          :key="chip.name"
          size="sm"
          variant="subtle"
          icon-right="lucide-x"
          :aria-label="__('Remove filter {0}', [chip.label])"
          @click="remove(chip.name)"
        >
          <!-- A slot, not `label`: Button lets `label` override aria-label. -->
          {{ chip.label }}
        </Button>
        <span
          class="ms-auto text-sm text-ink-gray-5 max-sm:basis-full max-sm:text-end"
        >
          {{ countLabel(search.total, __("1 article"), __("{0} articles")) }}
        </span>
      </div>
    </div>

    <template v-if="canSearch">
      <PortalSkeleton
        v-if="!search.rows.length && !search.isCurrent"
        variant="category-rows"
        :count="5"
      />
      <div v-else-if="search.rows.length" class="mt-1 flex flex-col">
        <PortalArticleList
          marked
          class="transition-opacity"
          :class="{ 'opacity-50': !search.isCurrent }"
          :articles="results"
        />
        <Button
          v-if="search.hasMore"
          class="mx-auto mt-4"
          size="md"
          :label="__('Load more')"
          :loading="search.isLoading && search.isCurrent"
          @click="search.loadMore"
        />
      </div>
      <div v-else class="flex flex-col items-center gap-1 py-16 text-center">
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
    </template>

    <section v-else-if="recent.length">
      <h2 class="border-b border-outline-gray-1 pb-2 text-sm text-ink-gray-5">
        {{ __("Recently viewed") }}
      </h2>
      <PortalArticleList :articles="recent" />
    </section>

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
import { useKnowledgeBase } from "@app/stores/knowledgeBase";
import { useRecent } from "@app/stores/recent";
import PortalArticleList from "@app/components/knowledge_base/PortalArticleList.vue";
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

const results = computed(() =>
  search.rows.map((row) => ({
    ...row,
    meta: articleMeta(row.category_label, row.minutes),
  })),
);
const recent = computed(() =>
  recentArticles.value.map((row) => ({
    ...row,
    meta: articleMeta(row.categoryName, row.minutes),
  })),
);

function clear() {
  query.value = "";
  input.value?.focus();
}

function remove(name: string) {
  selected.value = selected.value.filter((value) => value !== name);
}
</script>
