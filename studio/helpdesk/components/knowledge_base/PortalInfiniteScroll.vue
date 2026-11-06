<template>
  <div class="relative">
    <!-- Reaches up the list to load early. Remounts after each load, which measures it again. -->
    <div
      v-if="!loading && !failed"
      ref="trigger"
      class="pointer-events-none absolute bottom-0 h-[800px] w-px"
      aria-hidden="true"
    />
    <div v-if="failed" class="flex items-center justify-center gap-3 py-4">
      <span class="text-p-sm text-ink-gray-5">
        {{ __("Could not load more articles") }}
      </span>
      <Button :label="__('Try again')" @click="emit('loadMore')" />
    </div>
    <PortalSkeleton v-else-if="loading" variant="category-rows" :count="3" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button } from "frappe-ui";
import { useIntersectionObserver } from "@vueuse/core";
import { __ } from "@helpdesk/shared/translation";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";

defineProps<{ loading?: boolean; failed?: boolean }>();
const emit = defineEmits<{ loadMore: [] }>();

const trigger = ref<HTMLElement | null>(null);
useIntersectionObserver(trigger, ([entry]) => {
  if (entry.isIntersecting) emit("loadMore");
});
</script>
