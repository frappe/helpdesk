<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="__('Avg. First Response')"
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
  lineColor: "#F35555",
  gradientColor: { start: "#ee9d9f", end: "rgba(251,232,233,0)" },
};

const chartConfig = computed(() => {
  const _data = getAvgFirstResponseTimeResource.fetched
    ? getAvgFirstResponseTimeResource.data
    : props.data;

  const dates = _data.data.map((item: any) => item.date);
  const avg_time = _data.data.map((item: any) => item.avg_time);
  const average =
    formatTime(_data.average, { day: true, hour: true, minute: true }) || "0m";
  const _percentageChange = _data?.percentage_change;
  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };

  return {
    data: avg_time,
    dates,
    average,
    percentageChange,
  };
});

const getAvgFirstResponseTimeResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_avg_first_response_time",
  type: "GET",
  makeParams: () => {
    return {
      period: currentDuration.value.toLowerCase(),
    };
  },
});

const changeDuration = (period: string) => {
  currentDuration.value = period;
  getAvgFirstResponseTimeResource.submit();
};

onMounted(() => {
  if (!props.data?.data) {
    getAvgFirstResponseTimeResource.submit();
  }
});
</script>
