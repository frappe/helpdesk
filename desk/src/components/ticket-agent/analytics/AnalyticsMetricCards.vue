<template>
  <div class="flex flex-col gap-4">
    <div
      v-for="card in cards"
      :key="card.label"
      class="flex flex-col gap-2 rounded-md border border-outline-gray-1 bg-surface-base p-4"
    >
      <div class="flex items-center gap-1.5">
        <span class="text-base text-ink-gray-5">{{ card.label }}</span>
        <Tooltip :text="card.description">
          <LucideInfo class="size-3.5 text-ink-gray-5" />
        </Tooltip>
      </div>
      <span class="text-lg-medium text-ink-gray-8">
        {{ card.value ?? "–" }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideInfo from "~icons/lucide/info";
import type { AnalyticsMetrics } from "./types";
import { formatSeconds } from "./utils";

const props = defineProps<{ metrics: AnalyticsMetrics }>();

const cards = computed(() => [
  {
    label: __("Avg. agent response gap"),
    value: formatSeconds(props.metrics.avg_agent_gap),
    description: __("Average time to reply after a customer message"),
  },
  {
    label: __("Avg. customer response gap"),
    value: formatSeconds(props.metrics.avg_customer_gap),
    description: __("Average time the customer took to reply to an agent"),
  },
  {
    label: __("Total hold time"),
    value: formatSeconds(props.metrics.hold_time),
    description: __("Time on hold with the SLA clock paused"),
  },
]);
</script>
