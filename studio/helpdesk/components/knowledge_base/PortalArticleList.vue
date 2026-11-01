<template>
  <div>
    <PortalLink
      v-for="article in articles"
      :key="article.name"
      :to="ROUTES.article(article)"
      class="group flex cursor-pointer items-center gap-4 py-4 -mx-2.5 px-2.5 rounded-4 transition-colors hover:bg-surface-gray-1 relative after:absolute after:inset-x-2.5 after:bottom-0 after:h-px after:bg-[--outline-gray-1] last:after:hidden hover:after:opacity-0 [&:has(+*:hover)]:after:opacity-0 focus-visible:focus-ring"
      @mouseenter="prefetchOnHover(article.name)"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <p
          class="min-w-0 text-base-medium text-ink-gray-8 group-hover:text-ink-gray-9 truncate max-sm:whitespace-normal max-sm:line-clamp-2"
        >
          {{ article.title }}
        </p>
        <p
          v-if="article.excerpt"
          class="text-p-sm text-ink-gray-5 truncate max-sm:whitespace-normal max-sm:line-clamp-2"
        >
          {{ article.excerpt }}
        </p>
      </div>
      <span
        class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4 group-hover:text-ink-gray-6"
        aria-hidden="true"
      />
    </PortalLink>
  </div>
</template>

<script setup lang="ts">
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import PortalLink from "@app/components/ui/PortalLink.vue";
import { prefetchOnHover } from "@app/stores/knowledgeBase";

defineProps<{
  articles: {
    name: string;
    title: string;
    title_slug?: string;
    excerpt?: string;
  }[];
}>();
</script>
