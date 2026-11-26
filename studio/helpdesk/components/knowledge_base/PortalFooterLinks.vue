<template>
  <ul class="flex flex-col gap-2">
    <li v-for="link in links" :key="link.url + link.label">
      <a
        :href="link.url"
        v-bind="linkTarget(link.open_in_new_tab)"
        class="text-p-sm text-ink-gray-6 transition-colors hover:text-ink-gray-9 motion-reduce:transition-none"
      >
        {{ link.label }}
      </a>
    </li>
  </ul>
</template>

<script setup lang="ts">
import type { KnowledgeBaseLink } from "@helpdesk/shared/knowledgeBasePreview";
import { linkTarget } from "@helpdesk/shared/utils";

defineProps<{ links: KnowledgeBaseLink[] }>();
</script>
