<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="__('Avg. Resolution')"
      :text="average"
      :currentDuration="currentDuration"
      :percentageChange="percentageChange"
      :chartConfig="chartConfig"
      @changeDuration="changeDuration"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import CardBase from "./CardBase.vue";
import { createResource } from "frappe-ui";
import { formatTime } from "@/utils";
import { EChartsOption } from "echarts";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const currentDuration = ref("Last month");

const average = computed(() => {
  const _average = getAvgResolutionTimeResource.fetched
    ? getAvgResolutionTimeResource.data?.average
    : props.data?.average;
  return formatTime(_average, { day: true, hour: true, minute: true }) || "0m";
});

const percentageChange = computed(() => {
  const _percentageChange = getAvgResolutionTimeResource.fetched
    ? getAvgResolutionTimeResource.data?.percentage_change
    : props.data?.percentage_change;
  return {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };
});

const getAvgResolutionTimeResource = createResource({
  url: "helpdesk.api.agent_dashboard.get_avg_resolution_time",
  type: "GET",
  makeParams: () => {
    return {
      period: currentDuration.value.toLowerCase(),
    };
  },
});

const changeDuration = (period: string) => {
  currentDuration.value = period;
  getAvgResolutionTimeResource.submit();
};

const chartConfig = computed<EChartsOption>(() => {
  const isDataFetched = getAvgResolutionTimeResource.fetched;
  const _data = isDataFetched
    ? getAvgResolutionTimeResource.data?.data
    : props.data?.data;
  if (!_data) return {};

  const dates = _data.map((item) => item.date);
  const avg_time = _data.map((item) => item.avg_time);
  const _percentageChange = isDataFetched
    ? getAvgResolutionTimeResource.data?.percentage_change
    : props.data?.percentage_change;
  return {
    xAxis: {
      type: "category",
      data: dates,
      show: false,
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        data: avg_time,
        type: "line",
        symbol: "none",
      },
    ],
    color: _percentageChange > 0 ? "#F35555" : "#278F5E",
    grid: {
      left: 2,
      right: 2,
      top: 2,
      bottom: 2,
    },
  };
});

onMounted(() => {
  if (!props.data?.data) {
    getAvgResolutionTimeResource.submit();
  }
});
</script>
