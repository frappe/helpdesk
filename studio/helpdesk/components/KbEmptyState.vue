<template>
  <div
    class="flex flex-col items-center justify-center gap-4 py-16 text-center"
  >
    <!-- The agent portal's EmptyState "badge" variant (desk/.../EmptyState.vue): a glyph
         in a grey disc over a title over a narrower description, centred. Kept inside
         the root: a comment beside it makes this a multi-root component, and Vue then
         drops the caller's class — which is how the caller sizes this. -->
    <div
      class="flex items-center justify-center rounded-full bg-surface-gray-1"
      style="width: 58px; height: 58px"
    >
      <component :is="glyph" class="size-6 text-ink-gray-6" />
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="text-base font-medium text-ink-gray-6">{{ title }}</div>
      <div
        v-if="description"
        class="text-p-sm text-ink-gray-5"
        style="max-width: 15rem"
      >
        {{ description }}
      </div>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
// Lucide, to match the agent portal. Named rather than resolved at runtime so the
// build inlines only the glyphs the app actually uses.
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
    /** One of the keys in GLYPHS; anything else falls back to the article glyph. */
    icon?: keyof typeof GLYPHS;
  }>(),
  { icon: "article" }
);

const glyph = computed(() => GLYPHS[props.icon] || GLYPHS.article);
</script>
