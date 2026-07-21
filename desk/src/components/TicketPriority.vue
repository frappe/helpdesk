<template>
  <span
    v-if="priority"
    class="flex items-center gap-2"
    :class="{ 'me-1': iconOnly }"
  >
    <span class="flex h-3.5 w-3.5 shrink-0 items-center justify-center">
      <LucideTriangleAlert
        v-if="level === 'Urgent'"
        class="h-3.5 w-3.5 text-ink-red-5"
      />
      <svg
        v-else
        class="h-3 w-3"
        viewBox="0 0 10 12"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          x="0"
          y="8"
          width="1.5"
          height="4"
          rx="0.5"
          :class="barClass(2)"
        />
        <rect
          x="4"
          y="4"
          width="1.5"
          height="8"
          rx="0.5"
          :class="barClass(1)"
        />
        <rect
          x="8"
          y="0"
          width="1.5"
          height="12"
          rx="0.5"
          :class="barClass(0)"
        />
      </svg>
    </span>
    <span v-if="!iconOnly" class="truncate">{{ priority }}</span>
  </span>
</template>

<script setup lang="ts">
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { computed } from "vue";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";

const props = defineProps<{
  priority?: string;
  iconOnly?: boolean;
}>();

/** Tallest bars faded per level: High is fully solid, Low nearly empty. */
const FADED_BARS: Record<string, number> = {
  High: 0,
  Medium: 1,
  Low: 2,
};

const { getLevel } = useTicketPriorityStore();

const level = computed(() => getLevel(props.priority ?? ""));

function barClass(barIndexFromTop: number): string {
  const faded = FADED_BARS[level.value] ?? 0;
  return barIndexFromTop < faded ? "fill-ink-gray-3" : "fill-ink-gray-8";
}
</script>
