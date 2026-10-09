<template>
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
        <!-- The input leaves room for an icon, not the hint; typed text would run under it. -->
        <template v-if="!query" #suffix>
          <KeyboardShortcut
            combo="Mod+K"
            class="text-ink-gray-4 [@media(pointer:coarse)]:hidden"
          />
        </template>
      </TextInput>
    </div>

    <div
      ref="list"
      class="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto px-3 pb-4 pt-2"
    >
      <div v-for="category in visibleCategories" :key="category.name">
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
            :class="category.isCurrent ? 'text-ink-gray-8' : 'text-ink-gray-6'"
          >
            {{ category.label }}
          </span>
          <!-- In the label, not #suffix: only the button takes the click. -->
          <span
            class="lucide-chevron-right mr-1.5 size-4 shrink-0 text-ink-gray-5 transition-transform duration-150"
            :class="category.isOpen && 'rotate-90'"
          />
        </SidebarItem>

        <PortalCollapse
          :id="`kb-sidebar-${category.name}`"
          :open="category.isOpen"
        >
          <div
            class="mb-1.5 ml-4 mt-0.5 flex flex-col gap-0.5 border-l border-outline-gray-2 pl-2 pr-1"
          >
            <SidebarItem
              v-for="article in category.matches"
              :key="article.name"
              :route="ROUTES.article(article)"
              :active="article.name === activeName"
              :title="article.title"
              class="max-md:h-9 data-[state=active]:bg-surface-gray-2 data-[state=active]:shadow-none"
            >
              <template #prefix />
              <!-- -ml-2 takes back the gap SidebarItem leaves for an icon. -->
              <span class="-ml-2 min-w-0 truncate text-sm">{{
                article.title
              }}</span>
            </SidebarItem>
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
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import {
  Icon,
  KeyboardShortcut,
  Sidebar,
  SidebarItem,
  TextInput,
  useKeyboardShortcut,
} from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import PortalCollapse from "@app/components/common/PortalCollapse.vue";
import { ROUTES } from "@app/routes";
import { matchesQuery } from "@app/utils";

type Category = { name: string; category_name?: string; icon?: string | null };
type ArticleTitle = { name: string; title: string; category?: string | null };

// `activeCategory` opens a category on its own page, where no article is current.
const props = withDefaults(
  defineProps<{
    categories?: Category[];
    articles?: ArticleTitle[];
    activeName?: string;
    activeCategory?: string;
  }>(),
  {
    categories: () => [],
    articles: () => [],
    activeName: "",
    activeCategory: "",
  }
);

const query = ref("");
const openName = ref<string | null>(null);

const currentCategory = computed(
  () =>
    props.activeCategory ||
    props.articles.find((article) => article.name === props.activeName)
      ?.category
);

watch(currentCategory, (name) => name && (openName.value = name), {
  immediate: true,
});

function toggle(name: string) {
  if (query.value.trim()) return;
  openName.value = openName.value === name ? null : name;
}

const visibleCategories = computed(() => {
  const searching = Boolean(query.value.trim());
  return props.categories
    .map((category) => {
      const matches = props.articles.filter(
        (article) =>
          article.category === category.name &&
          matchesQuery(query.value, article.title)
      );
      return {
        name: category.name,
        label: category.category_name || category.name,
        icon: category.icon,
        matches,
        isCurrent: category.name === currentCategory.value,
        isOpen: searching
          ? matches.length > 0
          : openName.value === category.name,
      };
    })
    .filter((category) => !searching || category.matches.length);
});

// A long list leaves the current category or article out of sight, so bring it into view once
// per page, scrolling only the list.
const list = ref<HTMLElement | null>(null);
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

const search = ref<InstanceType<typeof TextInput> | null>(null);
useKeyboardShortcut({
  combo: "Mod+K",
  description: __("Search articles"),
  handler: () => search.value?.focus(),
});
</script>
