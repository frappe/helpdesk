<template>
  <div
    class="flex flex-col items-center justify-center gap-4 py-16 text-center"
  >
    <!-- Inside the root: a comment beside it makes this multi-root, and Vue then drops
         the caller's class, which is how the caller sizes this. -->
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
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
// Named, not resolved at runtime, so the build inlines only the glyphs in use.
import LucideBuilding2 from "~icons/lucide/building-2";
import LucideBookOpen from "~icons/lucide/book-open";
import LucideInbox from "~icons/lucide/inbox";
import LucideSearch from "~icons/lucide/search";
import LucideUsers from "~icons/lucide/users";

const GLYPHS = {
  organization: LucideBuilding2,
  article: LucideBookOpen,
  ticket: LucideInbox,
  search: LucideSearch,
  people: LucideUsers,
};

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    // One of the keys in GLYPHS; anything else falls back to the article glyph.
    icon?: keyof typeof GLYPHS;
  }>(),
  { icon: "article" }
);

const glyph = computed(() => GLYPHS[props.icon] || GLYPHS.article);
</script>
