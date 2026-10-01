<template>
  <RouterLink
    :to="ROUTES.article(article.name)"
    class="flex items-start gap-3 px-2 py-3 text-left no-underline"
    :class="
      variant === 'list'
        ? 'border-b border-outline-gray-1 transition-colors hover:bg-surface-gray-2'
        : 'border-outline-gray-1 [&:not(:last-child)]:border-b'
    "
  >
    <PortalArticleThumbnail
      :class="variant === 'list' && 'mt-px'"
      :src="variant === 'list' ? article.image : null"
      :bordered="variant === 'suggestion'"
    />
    <!-- Server text: escaped, with only the search highlighter's <mark> left in. -->
    <span
      class="flex min-w-0 flex-1 flex-col gap-0.5 [&_mark]:bg-transparent [&_mark]:font-semibold [&_mark]:text-ink-gray-9"
    >
      <span
        class="truncate text-base leading-[1.15] font-medium text-ink-gray-8"
        v-html="article.title"
      />
      <span
        class="line-clamp-1 text-p-sm"
        :class="variant === 'list' ? 'text-ink-gray-6' : 'text-ink-gray-5'"
        v-html="article.excerpt"
      />
      <span
        v-if="variant === 'list'"
        class="truncate text-p-xs text-ink-gray-4"
      >
        {{
          article.category_name
            ? `${__("Knowledge base")} / ${article.category_name}`
            : __("Knowledge base")
        }}
      </span>
    </span>
  </RouterLink>
</template>

<script setup lang="ts">
// An article in search results ("list") or under the new-ticket subject ("suggestion").
import { RouterLink } from "vue-router";
import { __ } from "@helpdesk/shared/translation";
import PortalArticleThumbnail from "@app/components/kb/PortalArticleThumbnail.vue";
import { ROUTES } from "@app/routes";

withDefaults(
  defineProps<{
    article: {
      name: string;
      title: string;
      excerpt?: string;
      image?: string | null;
      category_name?: string;
    };
    variant?: "list" | "suggestion";
  }>(),
  { variant: "list" }
);
</script>
