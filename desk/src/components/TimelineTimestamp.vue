<template>
  <Tooltip :text="tooltipText">
    <span :class="className">{{ displayText }}</span>
  </Tooltip>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Tooltip } from "frappe-ui";
import { dateFormat, dateTooltipFormat, timeAgo } from "@/utils";
import { useTimelinePreferences } from "@/composables/timelinePreferences";

const props = withDefaults(
  defineProps<{
    date: string;
    // Tooltip drops plain class fallthrough (inheritAttrs: false), so the
    // span's classes come in as an explicit prop
    className?: string;
  }>(),
  { className: "text-sm text-ink-gray-5" }
);

const { showExactTimestamp } = useTimelinePreferences();

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
