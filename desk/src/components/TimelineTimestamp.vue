<template>
  <Tooltip :text="tooltipText">
    <span :class="className">{{ displayText }}</span>
  </Tooltip>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Tooltip } from "frappe-ui";
import { storeToRefs } from "pinia";
import { dateFormat, dateTooltipFormat, timeAgo } from "@/utils";
import { useAuthStore } from "@/stores/auth";

const props = withDefaults(
  defineProps<{
    date: string;
    // Tooltip drops plain class fallthrough (inheritAttrs: false), so the
    // span's classes come in as an explicit prop
    className?: string;
  }>(),
  { className: "text-sm text-ink-gray-5" }
);

const { showExactTimestamp } = storeToRefs(useAuthStore());

const relative = computed(() => timeAgo(props.date));
const exact = computed(() => dateFormat(props.date, dateTooltipFormat));

// whichever format is not displayed stays available in the tooltip
const displayText = computed(() =>
  showExactTimestamp.value ? exact.value : relative.value
);
const tooltipText = computed(() =>
  showExactTimestamp.value ? relative.value : exact.value
);
</script>
