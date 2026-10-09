<template>
  <div
    class="flex flex-col items-center justify-center gap-4 py-16 text-center"
  >
    <div
      class="flex size-[58px] items-center justify-center rounded-full bg-surface-gray-1"
    >
      <component :is="glyph" class="size-6 text-ink-gray-6" />
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="text-base font-medium text-ink-gray-6">{{ title }}</div>
      <div v-if="description" class="max-w-60 text-p-sm text-ink-gray-5">
        {{ description }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import LucideBuilding2 from "~icons/lucide/building-2";
import LucideInbox from "~icons/lucide/inbox";
import PortalArticleIcon from "@app/components/knowledge_base/PortalArticleIcon.vue";

const GLYPHS = {
  organization: LucideBuilding2,
  article: PortalArticleIcon,
  ticket: LucideInbox,
};

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    icon?: keyof typeof GLYPHS;
  }>(),
  { icon: "article" }
);

const glyph = computed(() => GLYPHS[props.icon] || GLYPHS.article);
</script>
