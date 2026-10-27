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
        <!-- Rows already in hand beat the skeleton; enough rows to fill, clipped. -->
        <PortalSkeleton
          v-if="loading && !categories.length"
          variant="nav"
          :count="40"
          class="min-h-0 flex-1 overflow-hidden"
        />
        <!-- A group: its own articles, then its Subcategories' groups. -->
        <DefineGroup v-slot="{ category, nested }">
          <div :class="!nested && revealed && 'portal-reveal'">
            <SidebarItem
              class="max-md:h-11"
              :active="false"
              :aria-expanded="category.isOpen"
              :aria-controls="`kb-sidebar-${category.name}`"
              :data-current="category.name === currentCategory || undefined"
              @click="toggle(category.name, nested)"
            >
              <template #prefix>
                <Icon
                  :icon="categoryIcon(category.icon)"
                  class="size-4 max-md:size-[18px]"
                  :class="
                    category.isCurrent ? 'text-ink-gray-8' : 'text-ink-gray-6'
                  "
                />
              </template>
              <span
                class="min-w-0 flex-1 truncate text-sm max-md:text-base"
                :class="
                  category.isCurrent ? 'text-ink-gray-8' : 'text-ink-gray-6'
                "
              >
                {{ category.label }}
              </span>
              <!-- Not #suffix: only the button takes the click. -->
              <span
                class="lucide-chevron-right mr-[3px] size-4 shrink-0 text-ink-gray-5 transition-transform duration-150"
                :class="category.isOpen && 'rotate-90'"
              />
            </SidebarItem>

            <PortalCollapse
              :id="`kb-sidebar-${category.name}`"
              :open="category.isOpen"
              lazy
            >
              <div
                class="mb-1.5 ml-4 mt-0.5 flex flex-col gap-0.5 border-l border-outline-gray-2 pl-2 pr-1"
              >
                <SidebarItem
                  v-for="article in category.rows"
                  :key="article.name"
                  :data-article="article.name"
                  :route="ROUTES.article(article)"
                  :active="article.name === activeName"
                  :title="article.title"
                  class="max-md:h-11 data-[state=active]:bg-surface-gray-2 data-[state=active]:shadow-none"
                >
                  <template #prefix />
                  <!-- -ml-2 undoes SidebarItem's icon gap; pr-2 mirrors its pl-2. -->
                  <span
                    class="-ml-2 min-w-0 truncate pr-2 text-sm max-md:text-[15px]"
                  >
                    <template
                      v-for="(part, i) in splitMatch(article.title)"
                      :key="i"
                    >
                      <mark
                        v-if="i % 2"
                        class="rounded-sm bg-surface-amber-2 px-0.5 text-ink-gray-9"
                        >{{ part }}</mark
                      ><template v-else>{{ part }}</template>
                    </template>
                  </span>
                </SidebarItem>
                <button
                  v-if="category.hidden"
                  type="button"
                  class="flex h-7 items-center rounded-4 px-2 text-left text-sm text-ink-gray-5 hover:bg-surface-gray-2 max-md:h-11"
                  @click="showMore(category.name)"
                >
                  {{
                    __("Show {0} more", [Math.min(category.hidden, SHOW_STEP)])
                  }}
                </button>
                <ReuseGroup
                  v-for="subcategory in category.subcategories"
                  :key="subcategory.name"
                  :category="subcategory"
                  :nested="true"
                />
              </div>
            </PortalCollapse>
          </div>
        </DefineGroup>
        <ReuseGroup
          v-for="category in visibleCategories"
          :key="category.name"
          :category="category"
          :nested="false"
        />

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
import { createReusableTemplate, useMediaQuery, useScroll } from "@vueuse/core";
import { computed, nextTick, ref, useAttrs, watch } from "vue";
import {
  BottomSheet,
  Icon,
  Sidebar,
  SidebarItem,
  TextInput,
  useKeyboardShortcut,
} from "frappe-ui";
import ShortcutKey from "@helpdesk/shared/ShortcutKey.vue";
import { __ } from "@helpdesk/shared/translation";
import PortalCollapse from "@app/components/ui/PortalCollapse.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { categoryIcon } from "@helpdesk/shared/categoryIcons";
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
  icon?: string | null;
  rows: ArticleTitle[];
  hidden: number;
  matches: ArticleTitle[];
  subcategories: Group[];
  isCurrent: boolean;
  isOpen: boolean;
};

const [DefineGroup, ReuseGroup] = createReusableTemplate<{
  category: Group;
  nested: boolean;
}>();

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

// Search opens all matches; folds hold until the query changes.
const foldedInSearch = ref(new Set<string>());
watch(query, () => (foldedInSearch.value = new Set()));

function toggle(name: string, nested: boolean) {
  if (!query.value.trim()) {
    const open = nested ? openSubName : openName;
    open.value = open.value === name ? null : name;
    return;
  }
  const folded = new Set(foldedInSearch.value);
  folded.has(name) ? folded.delete(name) : folded.add(name);
  foldedInSearch.value = folded;
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

function toGroup(
  category: Category,
  searching: boolean,
  openRef: typeof openName
): Group {
  const articles = category.articles || [];
  const matches = searching
    ? articles.filter((article) => matchesQuery(query.value, article.title))
    : articles;
  // Always include the current article.
  const current = matches.findIndex(
    (article) => article.name === props.activeName
  );
  const limit = Math.max(
    sidebarState.shown[category.name] || SHOW_STEP,
    current + 1
  );
  // Sidebar rows come sorted by `category_name`.
  const subcategories = props.categories
    .filter((sub) => sub.parent_article_category === category.name)
    .map((sub) => toGroup(sub, searching, openSubName))
    .filter((sub) => !searching || sub.matches.length);
  return {
    rows: matches.slice(0, limit),
    hidden: Math.max(matches.length - limit, 0),
    name: category.name,
    label: category.category_name || category.name,
    icon: category.icon,
    matches,
    subcategories,
    isCurrent:
      category.name === currentCategory.value ||
      category.name === currentParent.value,
    isOpen: searching
      ? !foldedInSearch.value.has(category.name)
      : openRef.value === category.name,
  };
}

const visibleCategories = computed(() => {
  const searching = Boolean(query.value.trim());
  return props.categories
    .filter((category) => !category.parent_article_category)
    .map((category) => toGroup(category, searching, openName))
    .filter(
      (category) =>
        !searching || category.matches.length || category.subcategories.length
    );
});

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
