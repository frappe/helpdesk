<template>
  <div
    class="flex flex-col rounded-lg border border-outline-gray-1 bg-surface-white p-4"
  >
    <h3 class="text-lg font-semibold text-ink-gray-8">
      {{ __("Response Gap Over Time") }}
    </h3>
    <span class="text-base text-ink-gray-5">
      {{ __("Agent response time trend across the ticket.") }}
    </span>
    <div
      v-if="!gaps.length"
      class="flex h-40 items-center justify-center text-p-sm text-ink-gray-4"
    >
      {{ __("No agent replies yet") }}
    </div>
    <ECharts v-else :options="chartOptions" class="mt-2 h-40 w-full" />
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { dayjsLocal, ECharts } from "frappe-ui";
import { computed } from "vue";
import { formatSeconds, GapRow } from "./types";

const props = defineProps<{ gaps: GapRow[] }>();

const { getUser } = useUserStore();

// round duration steps, never decimal hours
const TICK_STEPS = [
  300, 600, 900, 1800, 3600, 7200, 14400, 28800, 57600, 86400, 172800,
];

const chartOptions = computed(() => {
  const values = props.gaps.map((g) => g.gap_seconds);
  const peak = Math.max(...values, 1);
  const step = TICK_STEPS.find((s) => peak / s <= 3) || 345600;
  const max = Math.ceil(peak / step) * step;
  return {
    animation: false,
    grid: { left: 8, right: 36, top: 12, bottom: 0, containLabel: true },
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const gap = props.gaps[params[0].dataIndex];
        const agent = getUser(gap.agent).full_name || gap.agent;
        const when = dayjsLocal(gap.replied_at).format("MMM D, h:mm a");
        return `${agent}<br/>${formatSeconds(gap.gap_seconds)} · ${when}`;
      },
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: props.gaps.map((g) => dayjsLocal(g.replied_at).format("MMM D, ha")),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: cssVar("--outline-gray-2") } },
      axisLabel: {
        color: cssVar("--ink-gray-5"),
        fontSize: 11,
        hideOverlap: true,
      },
    },
    yAxis: {
      type: "value",
      max,
      interval: step,
      axisLabel: {
        color: cssVar("--ink-gray-5"),
        fontSize: 11,
        formatter: (value: number) => (value ? formatSeconds(value) : "0"),
      },
      splitLine: {
        lineStyle: { type: "dotted", color: cssVar("--outline-gray-2") },
      },
    },
    series: [
      {
        type: "line",
        showSymbol: false,
        data: values,
        lineStyle: { width: 2, color: cssVar("--ink-blue-6") },
        // espresso tokens are oklch(); echarts' hover restyle can't parse
        // them and drops the line, so never enter the emphasis state
        emphasis: { disabled: true },
      },
    ],
  };
});

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}
</script>
