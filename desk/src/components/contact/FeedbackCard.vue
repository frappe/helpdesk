<template>
  <div
    class="sticky top-0 w-[240px] shrink-0 rounded-xl border border-outline-gray-2 bg-surface-white p-4"
  >
    <!-- Average rating -->
    <div class="flex items-center gap-3 mb-4">
      <div
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#FEF3C7]"
      >
        <LucideStar class="size-5 fill-[#F59E0B] text-[#F59E0B]" />
      </div>
      <div>
        <p class="text-2xl font-semibold text-ink-gray-9 leading-none">
          {{ avgRating }}
        </p>
        <p class="text-xs text-ink-gray-5 mt-0.5">
          {{ feedbackCount.data ?? 0 }} reviews
        </p>
      </div>
    </div>

    <!-- ECharts bar chart -->
    <ECharts :options="chartOptions" class="w-full h-[90px]" />
  </div>
</template>

<script setup lang="ts">
import { useContactFeedback } from "@/composables/contact";
import { EChartsOption } from "echarts";
import { ECharts } from "frappe-ui";
import { computed } from "vue";
import LucideStar from "~icons/lucide/star";

const props = defineProps<{
  name: string;
}>();

const { chartData, feedbackCount } = useContactFeedback(props.name);

const avgRating = 5;

const BAR_COLOR = "#E79913";

const hexToRgba = (hex: string, alpha: number) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
};

const chartOptions = computed<EChartsOption>(() => {
  const values = chartData;
  const opacities = [1, 0.7, 0.5, 0.3, 0.2];
  const uniqueSorted = [...new Set(values)].sort((a, b) => b - a);
  const opacityByIndex = values.map((v) => {
    const rank = uniqueSorted.indexOf(v);
    return opacities[Math.min(rank, opacities.length - 1)];
  });

  return {
    grid: { left: 4, right: 4, top: 16, bottom: 20, containLabel: false },
    xAxis: {
      type: "category",
      data: ["1", "2", "3", "4", "5"],
      axisLine: { show: true, lineStyle: { color: "#ededed" } },
      axisTick: { show: false },
      axisLabel: { color: "#6b7280", fontSize: 11 },
    },
    yAxis: { type: "value", show: false, min: 0 },
    series: [
      {
        type: "bar",
        data: values.map((value, i) => ({
          value,
          itemStyle: {
            color: hexToRgba(BAR_COLOR, opacityByIndex[i]),
            borderRadius: [4, 4, 0, 0],
          },
          label: {
            show: true,
            position: "top" as const,
            formatter: value > 0 ? String(value) : "",
            color: "#6b7280",
            fontSize: 11,
          },
        })),
        barWidth: 16,
        emphasis: { disabled: true },
      },
    ],
    tooltip: { show: false },
  };
});
</script>
