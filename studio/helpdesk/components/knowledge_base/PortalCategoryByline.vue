<template>
  <span
    v-if="creators.length"
    class="flex items-center gap-2 text-sm text-ink-gray-5"
  >
    <span class="flex ps-1.5">
      <Avatar
        v-for="creator in creators"
        :key="creator.name"
        class="-ms-1.5 ring-2 ring-[var(--surface-base)]"
        shape="circle"
        size="md"
        :image="creator.image"
        :label="creator.name"
      />
    </span>
    <span>{{ label }}</span>
    <span class="text-ink-gray-3">·</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Avatar } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";

const props = withDefaults(
  defineProps<{
    creators?: { name: string; image: string | null }[];
    creatorCount?: number;
  }>(),
  { creators: () => [], creatorCount: 0 }
);

const label = computed(() => {
  const first = props.creators[0].name.split(" ")[0];
  const others = Math.max(props.creatorCount, 1) - 1;
  if (!others) return __("By {0}", [first]);
  if (others === 1) return __("By {0} and 1 other", [first]);
  return __("By {0} and {1} others", [first, others]);
});
</script>
