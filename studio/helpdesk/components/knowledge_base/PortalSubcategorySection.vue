<template>
  <section class="flex w-full flex-col gap-1">
    <h2
      class="box-content flex h-7 items-center gap-2 border-b border-outline-gray-1 pb-2"
    >
      <span
        class="size-4 shrink-0 text-ink-gray-6"
        :class="category.icon || 'lucide-folder'"
        aria-hidden="true"
      />
      <PortalLink
        :to="ROUTES.category(category.name)"
        class="min-w-0 truncate rounded-sm text-lg-semibold text-ink-gray-8 hover:text-ink-gray-9 focus-visible:focus-ring"
      >
        {{ category.category_name }}
      </PortalLink>
      <span class="shrink-0 text-sm tabular-nums text-ink-gray-5">
        {{ category.article_count }}
      </span>
      <Button
        v-if="category.article_count > 4"
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
import { Button } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
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
