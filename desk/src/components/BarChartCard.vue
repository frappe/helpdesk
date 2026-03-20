<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="title"
      :text="chartData.text"
      :percentageChange="chartData.percentageChange"
      :chartConfig="hasData ? chartConfig : placeholderChartConfig"
      :currentDuration="currentDuration"
      :orientation="orientation"
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
  percentage_change: number;
  total?: number;
  average?: number;
  data: { date: string; count: number }[];
}

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  apiUrl: {
    type: String,
    required: true,
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
  negativeisBetter: {
    type: Boolean,
    default: true,
  },
});

const currentDuration = ref(__("Last month"));

const chartData = computed(() => {
  const isDataFetched = resource.fetched;
  const _data: BarChartData = isDataFetched ? resource.data : props.data;

  const labels = _data?.data?.map((item) => item.date) || [];
  const counts = _data?.data?.map((item) => item.count) || [];
  const _percentageChange = _data?.percentage_change || 0;

  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };

  return {
    labels,
    counts,
    percentageChange,
    text: props.measure === "average" ? _data?.average ?? 0 : _data?.total ?? 0,
  };
});

const hasData = computed(() => {
  const counts = chartData.value.counts as number[];
  return counts.length > 0 && counts.some((c) => c > 0);
});

const chartConfig = computed<EChartsOption>(() => {
  const color = props.barColor;

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
  url: props.apiUrl,
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
  resource.submit();
};

onMounted(() => {
  if (!props.data?.data) {
    resource.submit();
  }
});
</script>
