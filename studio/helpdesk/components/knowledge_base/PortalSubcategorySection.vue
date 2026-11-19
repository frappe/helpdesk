<template>
  <section
    class="overflow-hidden rounded-5 border border-outline-gray-2 bg-surface-base"
  >
    <h2>
      <PortalLink
        :to="ROUTES.category(category.name)"
        class="group flex items-center gap-2.5 border-b border-outline-gray-1 px-4 py-3 focus-visible:focus-ring"
      >
        <span
          class="size-4 shrink-0 text-ink-gray-7"
          :class="categoryIcon(category.icon)"
          aria-hidden="true"
        />
        <span class="min-w-0 flex-1 truncate text-base-medium text-ink-gray-9">
          {{ category.category_name }}
        </span>
        <span
          class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4 transition group-hover:text-ink-gray-8"
          aria-hidden="true"
        />
      </PortalLink>
    </h2>
    <div class="p-2">
      <PortalLink
        v-for="article in articles"
        :key="article.name"
        :to="ROUTES.article(article)"
        class="group flex items-center gap-2.5 rounded-4 px-2 py-1.5 transition-colors hover:bg-surface-gray-1 focus-visible:focus-ring"
        @mouseenter="prefetchOnHover(article.name)"
      >
        <ArticleIcon
          class="size-4 shrink-0 text-ink-gray-4 group-hover:text-ink-gray-6"
        />
        <span
          class="min-w-0 flex-1 truncate text-base text-ink-gray-8 group-hover:text-ink-gray-9"
        >
          {{ article.title }}
        </span>
      </PortalLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import ArticleIcon from "@helpdesk/shared/ArticleIcon.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { categoryIcon } from "@helpdesk/shared/categoryIcons";
import PortalLink from "@app/components/ui/PortalLink.vue";
import { prefetchOnHover } from "@app/stores/knowledgeBase";

// `articles` comes capped at 5 by get_subcategory_articles.
defineProps<{
  category: {
    name: string;
    category_name: string;
    icon?: string | null;
  };
  articles: {
    name: string;
    title: string;
    title_slug?: string;
  }[];
}>();
</script>
