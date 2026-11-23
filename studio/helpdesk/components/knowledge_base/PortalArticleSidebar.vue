<template>
  <!-- Phone: frappe-ui's sheet, which the section bar opens. Wider: a column. -->
  <component
    :is="isNarrow ? BottomSheet : 'div'"
    ref="panel"
    v-bind="wrapperProps"
  >
    <Sidebar
      :collapsible="false"
      width="100%"
      :aria-label="__('Knowledge base')"
      class="border-r border-outline-gray-1 !bg-surface-base max-md:!h-[calc(90dvh-6rem)] max-md:border-r-0"
    >
      <div class="px-3 pb-2 pt-4 max-md:px-4 max-md:pt-2">
        <TextInput
          ref="search"
          v-model="query"
          size="sm"
          variant="outline"
          class="[&_input]:!shadow-none max-md:[&_input]:h-11 max-md:[&_input]:text-base"
          :placeholder="__('Search articles')"
          @focus="isFocused = true"
          @blur="isFocused = false"
        >
          <template #prefix>
            <span class="lucide-search size-4 text-ink-gray-4" />
          </template>
          <template #suffix>
            <ShortcutKey
              v-if="searchShortcut && !query && !isFocused"
              class="[@media(pointer:coarse)]:hidden"
              size="sm"
              keys="/"
            />
          </template>
        </TextInput>
      </div>

      <!-- Mask fades rows under the search box once scrolled. -->
      <div
        ref="list"
        class="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto px-3 pb-4 pt-2"
        @pointerover="prefetchHovered"
        @focusin="prefetchHovered"
        :class="
          !arrivedState.top &&
          '[mask-image:linear-gradient(to_bottom,transparent,black_1.5rem)]'
        "
      >
        <!-- Rows already in hand beat the skeleton; enough rows to fill, clipped.
             Tree: a row click toggles a category and opens its page. -->
        <PortalSkeleton
          v-if="loading && !categories.length"
          variant="nav"
          :count="40"
          class="min-h-0 flex-1 overflow-hidden"
        />
        <Tree
          v-else
          :nodes="treeNodes"
          node-key="key"
          guides="lines"
          :expanded="expandedKeys"
          class="[--tree-indent:32px] motion-safe:[&_[role=group]]:animate-[portal-fade-in_150ms_ease-out] [--tree-row-height:28px] [&_[data-slot=row]:has(>[data-article])>span[aria-hidden]]:hidden [&_[data-slot=row]:has(>[data-more])>span[aria-hidden]]:hidden max-md:[--tree-row-height:44px] [&_[data-slot=row]:has([data-active])]:bg-surface-gray-2 [&>li]:[contain-intrinsic-size:auto_var(--tree-row-height)] [&>li]:[content-visibility:auto]"
          :class="revealed && 'portal-reveal'"
          @update:expanded="onExpanded"
        >
          <template #item-label="{ node }">
            <Button
              v-if="node.kind === 'more'"
              variant="ghost"
              data-more
              class="!h-auto !bg-transparent !px-0 !text-ink-gray-5 underline-offset-2 hover:!text-ink-gray-8 hover:underline"
              :label="__('Show {0} more', [Math.min(node.hidden, SHOW_STEP)])"
              @click="showMore(node.name)"
            />
            <RouterLink
              v-else-if="node.kind === 'category'"
              :to="ROUTES.category(node.name)"
              :data-current="marked[node.key] === 'current' || undefined"
              @click.stop="onCategoryClick(node.name, node.nested)"
              class="flex h-full min-w-0 flex-1 items-center text-sm max-md:text-base"
              :class="marked[node.key] ? 'text-ink-gray-8' : 'text-ink-gray-6'"
            >
              <span class="truncate">{{ node.label }}</span>
            </RouterLink>
            <RouterLink
              v-else
              :to="node.route"
              :title="node.label"
              :data-article="node.name"
              :data-active="marked[node.key] || undefined"
              :aria-current="marked[node.key] ? 'page' : undefined"
              class="flex h-full min-w-0 flex-1 items-center text-sm max-md:text-base"
              :class="marked[node.key] ? 'text-ink-gray-8' : 'text-ink-gray-6'"
            >
              <span class="truncate">
                <template v-for="(part, i) in splitMatch(node.label)" :key="i">
                  <mark
                    v-if="i % 2"
                    class="rounded-sm bg-surface-amber-2 px-0.5 text-ink-gray-9"
                    >{{ part }}</mark
                  ><template v-else>{{ part }}</template>
                </template>
              </span>
            </RouterLink>
          </template>
        </Tree>

        <p
          v-if="query.trim() && !visibleCategories.length"
          class="break-words px-2 py-4 text-sm text-ink-gray-5"
        >
          {{ __("No articles match “{0}”.", [query.trim()]) }}
        </p>
      </div>
    </Sidebar>
  </component>
</template>

<script setup lang="ts">
import { useMediaQuery, useScroll } from "@vueuse/core";
import { computed, nextTick, reactive, ref, useAttrs, watch } from "vue";
import { RouterLink } from "vue-router";
import {
  BottomSheet,
  Button,
  Sidebar,
  TextInput,
  Tree,
  useKeyboardShortcut,
  type TreeKey,
  type TreeNode,
} from "frappe-ui";
import ShortcutKey from "@helpdesk/shared/ShortcutKey.vue";
import { __ } from "@helpdesk/shared/translation";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { matchesQuery } from "@helpdesk/shared/utils";
import { prefetchOnHover, sidebarState } from "@app/stores/knowledgeBase";

type ArticleTitle = { name: string; title: string };
type Category = {
  name: string;
  category_name?: string;
  icon?: string | null;
  parent_article_category?: string | null;
  articles?: ArticleTitle[];
};
type Group = {
  name: string;
  label: string;
  rows: ArticleTitle[];
  hidden: number;
  matches: ArticleTitle[];
  subcategories: Group[];
};

// Studio's attrs go on the column, not the sheet, which renders in a portal.
defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    categories?: Category[];
    activeName?: string;
    activeCategory?: string;
    open?: boolean;
    loading?: boolean;
    // Off where the page's own search takes "/".
    searchShortcut?: boolean;
  }>(),
  {
    categories: () => [],
    activeName: "",
    activeCategory: "",
    open: false,
    searchShortcut: true,
  }
);

const emit = defineEmits<{ close: [] }>();

const attrs = useAttrs();
const isNarrow = useMediaQuery("(max-width: 767px)");
const wrapperProps = computed(() =>
  isNarrow.value
    ? {
        open: props.open,
        title: __("Browse articles"),
        "onUpdate:open": (open: boolean) => open || emit("close"),
      }
    : {
        ...attrs,
        class: [attrs.class, "flex h-full w-[239px] shrink-0 flex-col"],
      }
);

// Fade in only rows that replace the skeleton.
const revealed = ref(props.loading && !props.categories.length);

const panel = ref<HTMLElement | null>(null);
defineExpose({ rootRef: panel });

const query = sidebarState.query;
const { openName, openSubName } = sidebarState;

const currentCategory = computed(
  () =>
    props.activeCategory ||
    props.categories.find((category) =>
      category.articles?.some((article) => article.name === props.activeName)
    )?.name
);
const currentParent = computed(
  () =>
    props.categories.find((category) => category.name === currentCategory.value)
      ?.parent_article_category
);

// A Subcategory opens with its parent.
watch(
  [currentCategory, currentParent],
  ([name, parent]) => {
    if (!name) return;
    openName.value = parent || name;
    if (parent) openSubName.value = name;
  },
  { immediate: true }
);

// Rows read their mark by key, so a page change redraws only the rows it marks.
const marked = reactive<Record<string, "current" | "parent" | "active">>({});
watch(
  () =>
    [
      currentCategory.value && categoryKey(currentCategory.value),
      currentParent.value && categoryKey(currentParent.value),
      props.activeName && `article:${props.activeName}`,
    ] as const,
  ([current, parent, active], previous) => {
    previous?.forEach((key) => key && delete marked[key]);
    if (current) marked[current] = "current";
    if (parent) marked[parent] = "parent";
    if (active) marked[active] = "active";
  },
  { immediate: true }
);

// Pages past the current article, so its row shows.
watch(
  () => props.activeName,
  (name) => {
    const articles = props.categories.find(
      (category) => category.name === currentCategory.value
    )?.articles;
    const at = articles?.findIndex((article) => article.name === name) ?? -1;
    const shown = sidebarState.shown[currentCategory.value!] || SHOW_STEP;
    if (at >= shown) sidebarState.shown[currentCategory.value!] = at + 1;
  },
  { immediate: true }
);

// Search opens all matches; folds hold until the query changes.
const foldedInSearch = reactive(new Set<string>());
watch(query, () => foldedInSearch.clear());

function toggle(name: string, nested: boolean) {
  if (!query.value.trim()) {
    const open = nested ? openSubName : openName;
    open.value = open.value === name ? null : name;
    return;
  }
  if (!foldedInSearch.delete(name)) foldedInSearch.add(name);
}

// Its own page's row folds and opens; another category's row opens it.
function onCategoryClick(name: string, nested: boolean) {
  if (name === currentCategory.value) return toggle(name, nested);
  if (query.value.trim()) return foldedInSearch.delete(name);
  (nested ? openSubName : openName).value = name;
}

// First match only, as `matchesQuery` checks.
function splitMatch(title: string) {
  const needle = query.value.trim().toLowerCase();
  const at = needle ? title.toLowerCase().indexOf(needle) : -1;
  if (at < 0) return [title];
  return [
    title.slice(0, at),
    title.slice(at, at + needle.length),
    title.slice(at + needle.length),
  ];
}

// Paged so huge categories draw fast.
const SHOW_STEP = 50;

function showMore(name: string) {
  sidebarState.shown[name] =
    (sidebarState.shown[name] || SHOW_STEP) + SHOW_STEP;
}

// Built once per load: a scan per category is O(n²) through reactive proxies.
const subcategoriesOf = computed(() => {
  const byParent = new Map<string, Category[]>();
  for (const category of props.categories) {
    const parent = category.parent_article_category;
    if (!parent) continue;
    if (!byParent.has(parent)) byParent.set(parent, []);
    byParent.get(parent)!.push(category);
  }
  return byParent;
});

// Kept out of the groups, so a fold does not rebuild the tree.
function isOpen(name: string, nested: boolean) {
  if (query.value.trim()) return !foldedInSearch.has(name);
  return (nested ? openSubName : openName).value === name;
}

function toGroup(category: Category, searching: boolean): Group {
  const articles = category.articles || [];
  const matches = searching
    ? articles.filter((article) => matchesQuery(query.value, article.title))
    : articles;
  const limit = sidebarState.shown[category.name] || SHOW_STEP;
  // Sidebar rows come sorted by `category_name`.
  const subcategories = (subcategoriesOf.value.get(category.name) || [])
    .map((sub) => toGroup(sub, searching))
    .filter((sub) => !searching || sub.matches.length);
  return {
    rows: matches.slice(0, limit),
    hidden: Math.max(matches.length - limit, 0),
    name: category.name,
    label: category.category_name || category.name,
    matches,
    subcategories,
  };
}

const visibleCategories = computed(() => {
  const searching = Boolean(query.value.trim());
  return props.categories
    .filter((category) => !category.parent_article_category)
    .map((category) => toGroup(category, searching))
    .filter(
      (category) =>
        !searching || category.matches.length || category.subcategories.length
    );
});

type SidebarNode = TreeNode & {
  key: string;
  kind: "category" | "article" | "more";
  name: string;
};

function categoryKey(name: string) {
  return `category:${name}`;
}

// Keys are prefixed: an article and a category may share a name.
function toNode(group: Group, nested = false): SidebarNode {
  const articles = group.rows.map((article) => ({
    key: `article:${article.name}`,
    kind: "article" as const,
    name: article.name,
    label: article.title,
    route: ROUTES.article(article),
  }));
  const more = group.hidden
    ? [
        {
          key: `more:${group.name}`,
          kind: "more" as const,
          name: group.name,
          label: __("Show more"),
          hidden: group.hidden,
        },
      ]
    : [];
  return {
    key: categoryKey(group.name),
    kind: "category",
    name: group.name,
    label: group.label,
    nested,
    children: [
      ...articles,
      ...more,
      ...group.subcategories.map((sub) => toNode(sub, true)),
    ],
  };
}

const treeNodes = computed(() =>
  visibleCategories.value.map((group) => toNode(group))
);

function eachGroup(fn: (group: Group, nested: boolean) => void) {
  const walk = (groups: Group[], nested: boolean) =>
    groups.forEach((group) => {
      fn(group, nested);
      walk(group.subcategories, true);
    });
  walk(visibleCategories.value, false);
}

const expandedKeys = computed(() => {
  const keys: string[] = [];
  eachGroup(
    (group, nested) =>
      isOpen(group.name, nested) && keys.push(categoryKey(group.name))
  );
  return keys;
});

function onExpanded(keys: TreeKey[]) {
  const next = new Set(keys);
  const current = new Set(expandedKeys.value);
  eachGroup((group, nested) => {
    const key = categoryKey(group.name);
    if (next.has(key) !== current.has(key)) toggle(group.name, nested);
  });
}

// The list mounts with the page, and again with each sheet open: each mount
// gets the last scroll back. The current item scrolls into view once per page.
const list = ref<HTMLElement | null>(null);
const { arrivedState, y } = useScroll(list);
watch(y, (top) => list.value && (sidebarState.scrollTop = top));
let shownFor = "";
watch(
  () =>
    [
      props.activeName || currentCategory.value,
      visibleCategories.value.length,
      list.value,
    ] as const,
  async ([key, , element], previous) => {
    if (!element) return;
    if (element !== previous?.[2]) element.scrollTop = sidebarState.scrollTop;
    if (!key || key === shownFor) return;
    await nextTick();
    const target =
      element.querySelector('[aria-current="page"]') ||
      element.querySelector("[data-current]");
    if (!target) return;
    shownFor = key;
    const box = element.getBoundingClientRect();
    const top = target.getBoundingClientRect().top - box.top;
    if (top < 0 || top > box.height - 48) {
      element.scrollTop += top - box.height / 3;
    }
  },
  { flush: "post" }
);

function prefetchHovered(event: Event) {
  const row = (event.target as Element).closest?.(
    "[data-article]"
  ) as HTMLElement | null;
  prefetchOnHover(row?.dataset.article);
}

const search = ref<InstanceType<typeof TextInput> | null>(null);
const isFocused = ref(false);
useKeyboardShortcut({
  combo: "Slash",
  description: __("Search articles"),
  enabled: () => props.searchShortcut,
  handler: () => search.value?.focus(),
});
</script>
