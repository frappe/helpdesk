<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="title"
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
import { computed, onMounted, ref, type PropType } from "vue";
import CardBase from "./CardBase.vue";
import { createResource } from "frappe-ui";
import { formatTime } from "@/utils";
import { __ } from "@/translation";

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

const currentDuration = ref("Last month");

const chartConfig = computed(() => {
  const isDataFetched = resource.fetched;
  const _data = isDataFetched ? resource.data : props.data;

  const dates = _data?.data?.map((item: any) => item.date) || [];
  const avg_time = _data?.data?.map((item: any) => item.avg_time) || [];
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
