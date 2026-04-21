<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="title"
      :text="chartData.text"
      :percentageChange="chartData.percentageChange"
      :chartConfig="hasData ? chartConfig : placeholderChartConfig"
      :currentDuration="currentDuration"
      :orientation="orientation"
      :timelineFilter="timelineFilter"
      @changeDuration="changeDuration"
    >
      <template v-if="$slots.text" #text>
        <slot name="text" v-bind="{ text: chartData.text }" />
      </template>
    </CardBase>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { EChartsOption } from "echarts";
import { createResource } from "frappe-ui";
import { computed, onMounted, ref, type PropType } from "vue";
import CardBase from "./ChartCardBase.vue";

interface BarChartData {
  percentage_change?: number;
  total?: number;
  average?: number;
  data: { date: string; count: number }[] | Record<number, number>;
  total_reviews?: number;
}

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  apiUrl: {
    type: String,
    required: false,
  },
  data: {
    type: Object as PropType<BarChartData>,
    required: true,
  },
  barColor: {
    type: String,
    default: "#3BBDE5",
  },
  dt: {
    type: String,
    required: false,
  },
  dn: {
    type: String,
    required: false,
  },
  orientation: {
    type: String as PropType<"vertical" | "horizontal">,
    default: "vertical",
  },
  measure: {
    type: String as PropType<"total" | "average">,
    default: "total",
  },
  negativeIsBetter: {
    type: Boolean,
    default: true,
  },
  timelineFilter: {
    type: Boolean,
    default: true,
  },
});

const currentDuration = ref(__("Last month"));

const chartData = computed(() => {
  const isDataFetched = resource.fetched;
  const _data: BarChartData = isDataFetched ? resource.data : props.data;

  // Star-distribution shape: data is { 1: n, 2: n, ... }
  if (!props.timelineFilter && _data?.data && !Array.isArray(_data.data)) {
    const distribution = _data.data as Record<number, number>;
    const values = [1, 2, 3, 4, 5].map((s) => distribution[s] ?? 0);
    return {
      labels: ["1", "2", "3", "4", "5"],
      counts: values,
      percentageChange: getPercentageChange(0),
      text: _data?.average ?? 0,
      isStarDistribution: true,
    };
  }

  // Time-series shape: data is [{ date, count }, ...]
  const timeData = Array.isArray(_data?.data)
    ? (_data.data as { date: string; count: number }[])
    : [];
  const labels = timeData.map((item) => item.date);
  const counts = timeData.map((item) => item.count);
  const _percentageChange = _data?.percentage_change || 0;
  const percentageChange = getPercentageChange(_percentageChange);

  return {
    labels,
    counts,
    percentageChange,
    text: props.measure === "average" ? _data?.average ?? 0 : _data?.total ?? 0,
    isStarDistribution: false,
  };
});

function getPercentageChange(change: number) {
  if (props.negativeIsBetter) {
    return {
      icon: change > 0 ? "arrow-up-right" : "arrow-down-left",
      value: change > 0 ? `+${change}` : change,
      color: change > 0 ? "text-red-600" : "text-green-600",
    };
  } else {
    return {
      icon: change > 0 ? "arrow-up-right" : "arrow-down-left",
      value: change > 0 ? `+${change}` : change,
      color: change > 0 ? "text-green-600" : "text-red-600",
    };
  }
}

const hasData = computed(() => {
  const counts = chartData.value.counts as number[];
  return counts.length > 0 && counts.some((c) => c > 0);
});

const chartConfig = computed<EChartsOption>(() => {
  const color = props.barColor;

  if (chartData.value.isStarDistribution) {
    const values = chartData.value.counts as number[];
    // rank by value descending: index 0 = highest, 4 = lowest
    const opacities = [1, 0.7, 0.5, 0.3, 0.2];
    const baseColor = props.barColor; // #E79913

    // unique sorted counts descending (for tie-aware rank lookup)
    const uniqueSorted = [...new Set(values)].sort((a, b) => b - a);

    const opacityByIndex: number[] = values.map((v) => {
      const rank = uniqueSorted.indexOf(v); // same count → same rank
      return opacities[Math.min(rank, opacities.length - 1)];
    });

    // helper: hex + opacity → rgba
    const hexToRgba = (hex: string, alpha: number) => {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r},${g},${b},${alpha})`;
    };

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
            value: value === 0 ? 0 : value,
            itemStyle: {
              color: hexToRgba(baseColor, opacityByIndex[i]),
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
  }

  return {
    xAxis: {
      type: "category",
      data: chartData.value.labels,
      show: false,
      boundaryGap: true,
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        data: (chartData.value.counts as number[]).map((value) => ({
          value,
          itemStyle: {
            color: value === 0 ? "#e5e7eb" : color,
            borderRadius: [3, 3, 0, 0],
          },
        })),
        type: "bar",
        barMaxWidth: 12,
        barMinHeight: 4,
        emphasis: { disabled: true },
        label: { show: false },
      },
    ],
    grid: {
      left: 2,
      right: 2,
      top: 2,
      bottom: 2,
    },
    tooltip: {
      show: true,
      trigger: "axis",
      appendToBody: true,
      position: (point: number[]) => [point[0] + 12, point[1] - 50],
      axisPointer: { type: "none" },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        if (!p.value) return "";
        return `<span style="font-size:12px;color:#6b7280">${p.name}: <b style="color:#374151">${p.value}</b></span>`;
      },
    },
  };
});

const placeholderChartConfig = computed<EChartsOption>(() => {
  const placeholderValues = Array.from(
    { length: 7 },
    () => Math.floor(Math.random() * 8) + 3
  );
  return {
    xAxis: { type: "category", show: false, boundaryGap: true },
    yAxis: { type: "value", show: false },
    series: [
      {
        data: placeholderValues.map((value) => ({
          value,
          itemStyle: { color: "#f1f1f1", borderRadius: [3, 3, 0, 0] },
        })),
        type: "bar",
        barMaxWidth: 12,
        emphasis: { disabled: true },
      },
    ],
    grid: { left: 2, right: 2, top: 2, bottom: 2 },
    tooltip: { show: false },
    animation: false,
  };
});

const resource = createResource({
  url: props.apiUrl || "",
  type: "GET",
  makeParams: () => {
    const params: Record<string, any> = {
      period: currentDuration.value.toLowerCase(),
    };
    if (props.dt && props.dn) {
      params.dt = props.dt;
      params.dn = props.dn;
    }
    return params;
  },
});

const changeDuration = (period: string) => {
  currentDuration.value = period;
  if (props.apiUrl) resource.submit();
};

onMounted(() => {
  if (props.timelineFilter && props.apiUrl && !props.data?.data) {
    resource.submit();
  }
});
</script>
