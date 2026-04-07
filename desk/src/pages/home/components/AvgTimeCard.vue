<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="title"
      :text="chartData.average"
      :percentageChange="chartData.percentageChange"
      :chartConfig="chartConfig"
      :currentDuration="currentDuration"
      @changeDuration="changeDuration"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, type PropType } from "vue";
import CardBase from "./CardBase.vue";
import { createResource } from "frappe-ui";
import { formatTime } from "@/utils";
import { __ } from "@/translation";
import { EChartsOption } from "echarts";

interface AverageResponseData {
  percentage_change: number;
  average: number;
  data: { date: string; avg_time: number }[];
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
});

const currentDuration = ref(__("Last month"));

const chartData = computed(() => {
  const isDataFetched = resource.fetched;
  const _data: AverageResponseData = isDataFetched ? resource.data : props.data;

  const dates = _data?.data?.map((item) => item.date) || [];
  const avg_time = _data?.data?.map((item) => item.avg_time) || [];
  const _percentageChange = _data?.percentage_change || 0;

  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };

  const average =
    formatTime(_data?.average || 0, { day: true, hour: true, minute: true }) ||
    "0m";

  return {
    data: avg_time,
    dates,
    percentageChange,
    average,
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
  };
});

const resource = createResource({
  url: props.apiUrl,
  type: "GET",
  makeParams: () => {
    return {
      period: currentDuration.value.toLowerCase(),
    };
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
