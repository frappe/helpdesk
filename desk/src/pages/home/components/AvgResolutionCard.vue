<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="__('Avg. Resolution')"
      :text="chartConfig.average"
      :currentDuration="currentDuration"
      :percentageChange="chartConfig.percentageChange"
      :chartData="chartConfig.data"
      :chartDates="chartConfig.dates"
      @changeDuration="changeDuration"
      :chartColor="chartColor"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import CardBase from "./CardBase.vue";
import { createResource } from "frappe-ui";
import { formatTime } from "@/utils";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const currentDuration = ref("Last month");

const chartColor = {
  lineColor: "#7263E8",
  gradientColor: { start: "#a093ee", end: "rgba(239, 237, 252,0)" },
};

const chartConfig = computed(() => {
  const isDataFetched = getAvgResolutionTimeResource.fetched;
  const _data = isDataFetched ? getAvgResolutionTimeResource.data : props.data;

  const dates = _data.data.map((item: any) => item.date);
  const avg_time = _data.data.map((item: any) => item.avg_time);
  const _percentageChange = _data?.percentage_change;
  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };
  const average =
    formatTime(_data.average, { day: true, hour: true, minute: true }) || "0m";

  return {
    data: avg_time,
    dates,
    percentageChange,
    average,
  };
});

const getAvgResolutionTimeResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_avg_resolution_time",
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

onMounted(() => {
  if (!props.data?.data) {
    getAvgResolutionTimeResource.submit();
  }
});
</script>
