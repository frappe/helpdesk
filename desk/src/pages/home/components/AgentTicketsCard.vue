<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="__('My Tickets')"
      :text="chartData.total"
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
import { __ } from "@/translation";
import { EChartsOption } from "echarts";

interface Data {
  percentage_change: number;
  total: number;
  data: { date: string; count: number }[];
}

const props = defineProps({
  data: {
    type: Object as PropType<Data>,
    required: true,
  },
});

const currentDuration = ref(__("Last month"));

const chartColor = {
  lineColor: "#5597F3",
  gradientColor: { start: "#abccfc", end: "rgba(229,240,254,0)" },
};

const chartData = computed(() => {
  const _data: Data = getAgentTicketsResource.fetched
    ? getAgentTicketsResource.data
    : props.data;

  const _percentageChange = _data?.percentage_change || 0;
  const total = _data?.total || 0;
  const dates = _data?.data?.map((item) => item.date) || [];
  const counts = _data?.data?.map((item) => item.count) || [];

  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };

  return {
    data: counts,
    percentageChange,
    total,
    counts,
    dates,
  };
});

const chartConfig = computed<EChartsOption>(() => {
  const color = chartColor.lineColor;
  const gradientColor = chartColor.gradientColor;
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

const getAgentTicketsResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_agent_tickets",
  type: "GET",
  makeParams: () => {
    return {
      period: currentDuration.value.toLowerCase(),
    };
  },
});

const changeDuration = (period: string) => {
  currentDuration.value = period;
  getAgentTicketsResource.submit();
};

onMounted(() => {
  if (!props.data?.data) {
    getAgentTicketsResource.submit();
  }
});
</script>
