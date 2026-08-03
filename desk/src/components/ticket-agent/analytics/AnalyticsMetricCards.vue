<template>
  <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
    <div
      v-for="card in cards"
      :key="card.label"
      class="flex flex-col gap-2 rounded-lg border border-outline-gray-1 bg-surface-white p-4"
    >
      <span class="text-base text-ink-gray-5">{{ card.label }}</span>
      <span class="text-xl font-medium tabular-nums text-ink-gray-8">
        {{ card.value ?? "–" }}
      </span>
      <span class="text-p-sm leading-snug text-ink-gray-5">
        {{ card.description }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { computed } from "vue";
import { AnalyticsMetrics, formatSeconds } from "./types";

const props = defineProps<{ metrics: AnalyticsMetrics }>();

const cards = computed(() => [
  {
    label: __("Avg agent response gap"),
    value: formatSeconds(props.metrics.avg_agent_gap),
    description: __("Average time to reply after a customer message"),
  },
  {
    label: __("Time to resolution"),
    value: formatSeconds(props.metrics.resolution_time),
    description: __("Working time from ticket open to resolved"),
  },
  {
    label: __("Longest agent silence"),
    value: formatSeconds(props.metrics.longest_agent_silence),
    description: __("Worst single gap where the customer was waiting"),
  },
]);
</script>
