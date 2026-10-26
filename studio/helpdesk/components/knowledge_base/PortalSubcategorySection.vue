<template>
  <section class="flex w-full flex-col gap-1">
    <h2
      class="box-content flex h-7 items-center gap-2 border-b border-outline-gray-1 pb-2"
    >
      <Icon
        :icon="categoryIcon(category.icon)"
        class="size-4 shrink-0 text-ink-gray-6"
        aria-hidden="true"
      />
      <PortalLink
        :to="ROUTES.category(category.name)"
        class="min-w-0 truncate rounded-sm text-lg-semibold text-ink-gray-8 hover:text-ink-gray-9 focus-visible:focus-ring"
      >
        {{ category.category_name }}
      </PortalLink>
      <Button
        v-if="category.article_count > 5"
        variant="ghost"
        size="sm"
        class="ms-auto -me-2 shrink-0"
        :route="ROUTES.category(category.name)"
        :aria-label="
          __('View all {0} articles in {1}', [
            category.article_count,
            category.category_name,
          ])
        "
      >
        {{ __("View all") }}
      </Button>
    </h2>
    <PortalArticleList :articles="articles.slice(0, 4)" />
  </section>
</template>

<script setup lang="ts">
import { Button, Icon } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { categoryIcon } from "@helpdesk/shared/categoryIcons";
import PortalLink from "@app/components/ui/PortalLink.vue";
import PortalArticleList from "./PortalArticleList.vue";

defineProps<{
  category: {
    name: string;
    category_name: string;
    icon?: string | null;
    article_count: number;
  };
  articles: {
    name: string;
    title: string;
    title_slug?: string;
    excerpt?: string;
  }[];
}>();
</script>
