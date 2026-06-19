<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="title"
      :text="chartData.text"
      :percentageChange="chartData.percentageChange"
      :chartConfig="chartConfig"
      :currentDuration="currentDuration"
      :orientation="orientation"
      :timelineFilter="timelineFilter"
      @changeDuration="changeDuration"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { formatTime } from "@/utils";
import { EChartsOption } from "echarts";
import { createResource } from "frappe-ui";
import { computed, onMounted, ref, type PropType } from "vue";
import CardBase from "./ChartCardBase.vue";

interface AverageResponseData {
  percentage_change: number;
  average?: number;
  total?: number;

  data: { date: string; avg_time?: number; count?: number }[];
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
  timelineFilter: {
    type: Boolean,
    default: true,
  },
  data: {
    type: Object as PropType<AverageResponseData>,
    required: true,
  },
  chartColor: {
    type: Object as PropType<{
      lineColor: string;
      gradientColor: { start: string; end: string };
    }>,
    required: true,
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
  type: {
    type: String as PropType<"Time" | "Count">,
    default: "Time",
  },
});

const currentDuration = ref(__("Last month"));

const chartData = computed(() => {
  const isDataFetched = resource.fetched;
  const _data: AverageResponseData = isDataFetched ? resource.data : props.data;

  const dates = _data?.data?.map((item) => item.date) || [];

  const seriesData =
    _data?.data?.map((item) =>
      props.type === "Time" ? item.avg_time : item.count
    ) || [];
  const _percentageChange = _data?.percentage_change || 0;

  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };

  // for time take average and for count take total
  const text =
    props.type === "Time"
      ? formatTime(_data?.average || 0, {
          day: true,
          hour: true,
          minute: true,
          maxUnits: 2,
        }) || "0m"
      : _data?.total || 0;

  return {
    data: seriesData,
    dates,
    percentageChange,
    text,
  };
});

const chartConfig = computed<EChartsOption>(() => {
  const color = props.chartColor.lineColor;
  const gradientColor = props.chartColor.gradientColor;
  return {
    xAxis: {
      type: "category",
      data: chartData.value.dates,
      show: false,
      boundaryGap: false,
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        data: chartData.value.data,
        type: "line",
        symbol: "none",
        lineStyle: {
          width: 1.25,
        },
        areaStyle: {
          opacity: 0.8,
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: gradientColor.start,
              },
              {
                offset: 1,
                color: gradientColor.end,
              },
            ],
            global: false,
          },
        },
      },
    ],
    color: color,
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
      // position: (point: number[]) => [point[0] + 12, point[1] - 50],
      axisPointer: { type: "none" },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        if (p.value === undefined || p.value === null) return "";
        const value =
          props.type === "Time"
            ? formatTime(Number(p.value) || 0, {
                day: true,
                hour: true,
                minute: true,
                maxUnits: 2,
              }) || "0m"
            : p.value;
        return `<span style="font-size:12px;color:#6b7280">${p.name}: <b style="color:#374151">${value}</b></span>`;
      },
    },
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
