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
      <!-- A link styled as the search box: the search page does the searching. -->
      <div v-if="showSearch" class="px-3 pb-2 pt-4 max-md:pt-2">
        <RouterLink
          :to="searchRoute"
          class="flex h-7 items-center gap-2 rounded-4 border border-outline-gray-2 bg-surface-base px-2 text-base text-ink-gray-4 transition-colors hover:border-outline-gray-3 focus-visible:focus-ring max-md:h-11"
        >
          <span class="lucide-search size-4 shrink-0" aria-hidden="true" />
          <span class="min-w-0 flex-1 truncate">{{
            __("Search articles")
          }}</span>
          <ShortcutKey
            v-if="searchShortcut"
            class="[@media(pointer:coarse)]:hidden"
            aria-hidden="true"
            size="sm"
            keys="/"
          />
        </RouterLink>
      </div>

      <!-- Mask fades rows under the search box once scrolled. -->
      <div
        ref="list"
        class="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto px-3 pb-4"
        :class="[
          showSearch ? 'pt-2' : 'pt-4',
          !arrivedState.top &&
            '[mask-image:linear-gradient(to_bottom,transparent,black_1.5rem)]',
        ]"
      >
        <!-- Rows already in hand beat the skeleton; enough rows to fill, clipped. -->
        <PortalSkeleton
          v-if="loading && !categories.length"
          variant="nav"
          :count="40"
          class="min-h-0 flex-1 overflow-hidden"
        />
        <div
          v-for="category in topLevel"
          :key="category.name"
          :class="revealed && 'portal-reveal'"
        >
          <SidebarItem
            :route="ROUTES.category(category.name)"
            :active="category.name === activeCategory"
            :class="ROW_CLASS"
          >
            <template #prefix>
              <Icon
                :icon="categoryIcon(category.icon)"
                class="size-4 max-md:size-[18px]"
                :class="
                  category.name === openName
                    ? 'text-ink-gray-8'
                    : 'text-ink-gray-6'
                "
              />
            </template>
            <span
              class="min-w-0 truncate pr-2 text-sm max-md:text-[15px]"
              :class="category.name === openName && 'text-ink-gray-8'"
            >
              {{ category.category_name || category.name }}
            </span>
          </SidebarItem>

          <!-- The line sits on the icon's centre; labels start under the parent's. -->
          <div
            v-if="category.name === openName && children.length"
            class="mb-1.5 ml-4 mt-0.5 flex flex-col gap-0.5 border-l border-outline-gray-2 pl-[7px] max-md:ml-[17px] max-md:pl-2"
          >
            <SidebarItem
              v-for="child in children"
              :key="child.name"
              :route="ROUTES.category(child.name)"
              :active="child.name === activeCategory"
              :class="ROW_CLASS"
            >
              <template #prefix />
              <!-- -ml-2 undoes SidebarItem's icon gap. -->
              <span
                class="-ml-2 min-w-0 truncate pr-2 text-sm max-md:text-[15px]"
              >
                {{ child.category_name || child.name }}
              </span>
            </SidebarItem>
          </div>
        </div>
      </div>
    </Sidebar>
  </component>
</template>

<script setup lang="ts">
import { useMediaQuery, useScroll } from "@vueuse/core";
import { computed, nextTick, ref, useAttrs, watch } from "vue";
import { RouterLink, useRouter } from "vue-router";
import {
  BottomSheet,
  Icon,
  Sidebar,
  SidebarItem,
  useKeyboardShortcut,
} from "frappe-ui";
import ShortcutKey from "@helpdesk/shared/ShortcutKey.vue";
import { __ } from "@helpdesk/shared/translation";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { categoryIcon } from "@helpdesk/shared/categoryIcons";
import { sidebarState } from "@app/stores/knowledgeBase";

type Category = {
  name: string;
  category_name?: string;
  icon?: string | null;
  parent_article_category?: string | null;
};

// Same row at every level; the fill ends on one right edge.
const ROW_CLASS =
  "max-md:h-11 data-[state=active]:bg-surface-gray-2 data-[state=active]:shadow-none data-[state=inactive]:hover:bg-surface-gray-1";

// Studio's attrs go on the column, not the sheet, which renders in a portal.
defineOptions({ inheritAttrs: false });

const props = withDefaults(
  defineProps<{
    categories?: Category[];
    activeCategory?: string;
    // Only a category page scopes the search link.
    searchCategory?: string;
    open?: boolean;
    loading?: boolean;
    // Off on the search page, which has its own box.
    showSearch?: boolean;
    // Off where the page's own search takes "/".
    searchShortcut?: boolean;
  }>(),
  {
    categories: () => [],
    activeCategory: "",
    searchCategory: "",
    open: false,
    showSearch: true,
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

// Rows come sorted by `category_name`.
const topLevel = computed(() =>
  props.categories.filter((category) => !category.parent_article_category)
);

// The current category, or the parent of the current Subcategory.
const openName = computed(() => {
  const current = props.categories.find(
    (category) => category.name === props.activeCategory
  );
  return current?.parent_article_category || current?.name;
});

const children = computed(() => {
  if (!openName.value) return [];
  return props.categories.filter(
    (category) => category.parent_article_category === openName.value
  );
});

const searchRoute = computed(() =>
  ROUTES.search(
    props.searchCategory ? { category: props.searchCategory } : undefined
  )
);

const router = useRouter();
useKeyboardShortcut({
  combo: "Slash",
  description: __("Search articles"),
  enabled: () => props.showSearch && props.searchShortcut,
  handler: () => router.push(searchRoute.value),
});

// The list mounts with the page, and again with each sheet open: each mount
// gets the last scroll back. The current row scrolls into view once per page.
const list = ref<HTMLElement | null>(null);
const { arrivedState, y } = useScroll(list);
watch(y, (top) => list.value && (sidebarState.scrollTop = top));
let shownFor = "";
watch(
  () => [props.activeCategory, topLevel.value.length, list.value] as const,
  async ([key, , element], previous) => {
    if (!element) return;
    if (element !== previous?.[2]) element.scrollTop = sidebarState.scrollTop;
    if (!key || key === shownFor) return;
    await nextTick();
    const target = element.querySelector('[aria-current="page"]');
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
</script>
