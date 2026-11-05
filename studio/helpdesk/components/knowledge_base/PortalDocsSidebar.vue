<template>
  <aside
    class="hidden w-64 shrink-0 flex-col gap-6 overflow-y-auto border-r border-outline-gray-1 px-3 py-6 md:flex"
  >
    <RouterLink
      :to="ROUTES.home"
      class="flex h-7 items-center gap-2 rounded-[6px] px-2 text-base text-ink-gray-7 hover:bg-surface-gray-2"
    >
      <span class="lucide-arrow-left size-4 shrink-0" />
      {{ __("Help center") }}
    </RouterLink>

    <nav
      v-if="links.length"
      :aria-label="__('Related')"
      class="flex flex-col gap-0.5"
    >
      <span class="px-2 pb-1 text-sm text-ink-gray-5">{{ __("Related") }}</span>
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="rounded-[6px] px-2 py-1.5 text-base text-ink-gray-7 hover:bg-surface-gray-2"
      >
        {{ link.title }}
      </RouterLink>
    </nav>

    <a
      :href="siteUrl"
      target="_blank"
      rel="noopener"
      class="mt-auto flex h-7 items-center gap-2 rounded-[6px] px-2 text-base text-ink-gray-7 hover:bg-surface-gray-2"
    >
      <span class="lucide-external-link size-4 shrink-0" />
      {{ __("All docs") }}
    </a>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { __ } from "@helpdesk/shared/translation";

type Related = {
  docs: { route: string; title: string }[];
  articles: { name: string; title: string; title_slug?: string }[];
};

const props = defineProps<{ related?: Related; siteUrl: string }>();

const links = computed(() => [
  ...(props.related?.docs || []).map(({ route, title }) => ({
    to: ROUTES.docsPage(route),
    title,
  })),
  ...(props.related?.articles || []).map((article) => ({
    to: ROUTES.article(article),
    title: article.title,
  })),
]);
</script>
