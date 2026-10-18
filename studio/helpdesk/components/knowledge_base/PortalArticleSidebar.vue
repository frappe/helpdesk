<template>
  <div
    ref="panel"
    v-bind="$attrs"
    class="flex h-full w-[239px] shrink-0 flex-col transition-[transform,visibility] duration-200 ease-out motion-reduce:transition-none max-md:fixed max-md:inset-y-0 max-md:start-0 max-md:z-40 max-md:w-[min(320px,85vw)] max-md:bg-surface-base max-md:shadow-2xl"
    :class="
      !open &&
      'max-md:invisible max-md:-translate-x-full max-md:rtl:translate-x-full'
    "
  >
    <Sidebar
      :collapsible="false"
      width="100%"
      :aria-label="__('Knowledge base')"
      class="border-r border-outline-gray-1 !bg-surface-base"
    >
      <div class="px-3 pb-2 pt-4">
        <TextInput
          ref="search"
          v-model="query"
          size="sm"
          variant="outline"
          class="[&_input]:!shadow-none"
          :placeholder="__('Search articles')"
        >
          <template #prefix>
            <span class="lucide-search size-4 text-ink-gray-4" />
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
        <PortalSkeleton v-if="loading" variant="nav" :count="12" />
        <div
          v-for="category in visibleCategories"
          :key="category.name"
          :class="revealed && 'portal-reveal'"
        >
          <SidebarItem
            class="max-md:h-9"
            :active="false"
            :aria-expanded="category.isOpen"
            :aria-controls="`kb-sidebar-${category.name}`"
            :data-current="category.isCurrent || undefined"
            @click="toggle(category.name)"
          >
            <template #prefix>
              <Icon
                :icon="category.icon || 'lucide-folder'"
                class="size-4"
                :class="
                  category.isCurrent ? 'text-ink-gray-8' : 'text-ink-gray-6'
                "
              />
            </template>
            <span
              class="min-w-0 flex-1 truncate text-sm"
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
                class="max-md:h-9 data-[state=active]:bg-surface-gray-2 data-[state=active]:shadow-none"
              >
                <template #prefix />
                <!-- -ml-2 undoes SidebarItem's icon gap; pr-2 mirrors its pl-2. -->
                <span class="-ml-2 min-w-0 truncate pr-2 text-sm">
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
                class="flex h-7 items-center rounded-4 px-2 text-left text-sm text-ink-gray-5 hover:bg-surface-gray-2 max-md:h-9"
                @click="showMore(category.name)"
              >
                {{
                  __("Show {0} more", [Math.min(category.hidden, SHOW_STEP)])
                }}
              </button>
            </div>
          </PortalCollapse>
        </div>

        <p
          v-if="query.trim() && !visibleCategories.length"
          class="break-words px-2 py-4 text-sm text-ink-gray-5"
        >
          {{ __("No articles match “{0}”.", [query.trim()]) }}
        </p>
      </div>
    </Sidebar>
  </div>
  <div
    v-if="open"
    class="fixed inset-0 z-30 bg-black-overlay-500 md:hidden"
    @click="emit('close')"
  />
</template>

<script setup lang="ts">
import { useScroll } from "@vueuse/core";
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import {
  Icon,
  Sidebar,
  SidebarItem,
  TextInput,
  useKeyboardShortcut,
} from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import PortalCollapse from "@app/components/ui/PortalCollapse.vue";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { matchesQuery } from "@helpdesk/shared/utils";
import { prefetchOnHover, sidebarState } from "@app/stores/knowledgeBase";

type ArticleTitle = { name: string; title: string };
type Category = {
  name: string;
  category_name?: string;
  icon?: string | null;
  articles?: ArticleTitle[];
};

// Two roots: Studio's attrs go on the drawer, exposed as `rootRef`.
defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    categories?: Category[];
    activeName?: string;
    activeCategory?: string;
    open?: boolean;
    loading?: boolean;
  }>(),
  {
    categories: () => [],
    activeName: "",
    activeCategory: "",
    open: false,
  }
);

const emit = defineEmits<{ close: [] }>();

// Fade in only rows that replace the skeleton.
const revealed = ref(props.loading);

const panel = ref<HTMLElement | null>(null);
defineExpose({ rootRef: panel });

const query = sidebarState.query;
const openName = sidebarState.openName;

const currentCategory = computed(
  () =>
    props.activeCategory ||
    props.categories.find((category) =>
      category.articles?.some((article) => article.name === props.activeName)
    )?.name
);

watch(currentCategory, (name) => name && (openName.value = name), {
  immediate: true,
});

// Search opens all matches; folds hold until the query changes.
const foldedInSearch = ref(new Set<string>());
watch(query, () => (foldedInSearch.value = new Set()));

function toggle(name: string) {
  if (!query.value.trim()) {
    openName.value = openName.value === name ? null : name;
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

const visibleCategories = computed(() => {
  const searching = Boolean(query.value.trim());
  return props.categories
    .map((category) => {
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
      return {
        rows: matches.slice(0, limit),
        hidden: Math.max(matches.length - limit, 0),
        name: category.name,
        label: category.category_name || category.name,
        icon: category.icon,
        matches,
        isCurrent: category.name === currentCategory.value,
        isOpen: searching
          ? !foldedInSearch.value.has(category.name)
          : openName.value === category.name,
      };
    })
    .filter((category) => !searching || category.matches.length);
});

// Scroll the current item into view once per page, list only.
const list = ref<HTMLElement | null>(null);
const { arrivedState } = useScroll(list);
onMounted(() => list.value && (list.value.scrollTop = sidebarState.scrollTop));
onBeforeUnmount(
  () => list.value && (sidebarState.scrollTop = list.value.scrollTop)
);
let shownFor = "";
watch(
  () => [
    props.activeName || currentCategory.value,
    visibleCategories.value.length,
  ],
  async ([key]) => {
    if (!key || key === shownFor || !list.value) return;
    await nextTick();
    const target =
      list.value.querySelector('[aria-current="page"]') ||
      list.value.querySelector("[data-current]");
    if (!target) return;
    shownFor = key as string;
    const box = list.value.getBoundingClientRect();
    const top = target.getBoundingClientRect().top - box.top;
    if (top < 0 || top > box.height - 48) {
      list.value.scrollTop += top - box.height / 3;
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
useKeyboardShortcut({
  combo: "Slash",
  description: __("Search articles"),
  handler: () => search.value?.focus(),
});
</script>
