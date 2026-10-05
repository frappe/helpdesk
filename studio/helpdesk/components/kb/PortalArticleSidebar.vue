<template>
  <nav
    :aria-label="__('Knowledge base')"
    class="flex h-full flex-col border-r border-outline-gray-1 bg-surface-sidebar"
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
      class="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto px-3 pb-4 pt-1"
    >
      <div v-for="category in visibleCategories" :key="category.name">
        <button
          type="button"
          class="flex h-9 w-full items-center gap-2 rounded-4 pl-2 pr-1.5 md:h-7 text-left transition hover:bg-surface-gray-2"
          :aria-expanded="category.isOpen"
          :aria-controls="`kb-sidebar-${category.name}`"
          @click="toggle(category.name)"
        >
          <Icon
            :icon="category.icon || 'lucide-folder'"
            class="size-4 shrink-0"
            :class="category.isCurrent ? 'text-ink-gray-8' : 'text-ink-gray-6'"
          />
          <span
            class="min-w-0 flex-1 truncate text-sm leading-tighter"
            :class="category.isCurrent ? 'text-ink-gray-8' : 'text-ink-gray-6'"
          >
            {{ category.label }}
          </span>
          <span
            class="lucide-chevron-right size-4 shrink-0 text-ink-gray-5 transition-transform duration-150"
            :class="category.isOpen && 'rotate-90'"
          />
        </button>

        <PortalCollapse
          :id="`kb-sidebar-${category.name}`"
          :open="category.isOpen"
        >
          <div
            class="mb-1.5 ml-4 mt-0.5 flex flex-col gap-0.5 border-l border-outline-gray-2 pl-2 pr-1"
          >
            <RouterLink
              v-for="article in category.matches"
              :key="article.name"
              :to="ROUTES.article(article.name)"
              :aria-current="article.name === activeName ? 'page' : undefined"
              :title="article.title"
              class="flex min-h-9 items-center rounded-4 px-2 py-1.5 md:min-h-7 text-sm leading-snug no-underline transition"
              :class="
                article.name === activeName
                  ? 'bg-surface-elevation-3 text-ink-gray-8 shadow-sm'
                  : 'text-ink-gray-6 hover:bg-surface-gray-2'
              "
            >
              <span class="min-w-0 truncate">{{ article.title }}</span>
            </RouterLink>
          </div>
        </PortalCollapse>
      </div>

      <p
        v-if="query.trim() && !visibleCategories.length"
        class="px-2 py-4 text-sm text-ink-gray-5"
      >
        {{ __("No articles match “{0}”.", [query.trim()]) }}
      </p>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import {
  Icon,
  KeyboardShortcut,
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

const search = ref<InstanceType<typeof TextInput> | null>(null);
useKeyboardShortcut({
  combo: "Mod+K",
  description: __("Search articles"),
  handler: () => search.value?.focus(),
});
</script>
