<template>
  <div class="flex flex-col">
    <h3 class="text-base font-medium text-gray-900 mb-4">Today's trends</h3>
    <div class="flex gap-6">
      <!-- Chart Area -->
      <div class="flex-1">
        <div class="h-56">
          <AxisChart v-if="chartConfig" :config="chartConfig" />
          <div v-else class="flex items-center justify-center h-full text-gray-400">
            <span class="text-sm">No ticket data for this period</span>
          </div>
        </div>
        <!-- Legend -->
        <div class="flex items-center gap-6 mt-4 text-sm">
          <div class="flex items-center gap-2">
            <span class="w-4 h-0.5 bg-[#318AD8] rounded"></span>
            <span class="text-gray-600">Today</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-4 h-0.5 bg-gray-400 rounded"></span>
            <span class="text-gray-600">Yesterday</span>
          </div>
        </div>
      </div>

      <!-- Summary Metrics -->
      <div class="flex flex-col gap-4 min-w-[160px] border-l border-gray-100 pl-6">
        <div class="flex flex-col">
          <span class="text-xs text-gray-500 uppercase tracking-wide">Received</span>
          <span class="text-2xl font-semibold text-gray-900">{{ summaryMetrics.received }}</span>
        </div>
        <div class="flex flex-col">
          <span class="text-xs text-gray-500 uppercase tracking-wide">Average First...</span>
          <span class="text-2xl font-semibold text-gray-900">{{ formatTime(summaryMetrics.avgFirstResponse) }}</span>
        </div>
        <div class="flex flex-col">
          <span class="text-xs text-gray-500 uppercase tracking-wide">Resolution an...</span>
          <span class="text-2xl font-semibold text-gray-900">{{ summaryMetrics.resolutionRate }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { AxisChart } from "frappe-ui";

interface HourlyDataPoint {
  hour: number;
  count: number;
}

interface SummaryMetrics {
  received: number;
  avgFirstResponse: number;
  resolutionRate: number;
}

interface Props {
  todayData: HourlyDataPoint[];
  yesterdayData: HourlyDataPoint[];
  summaryMetrics: SummaryMetrics;
}

const props = defineProps<Props>();

const chartConfig = computed(() => {
  if (!props.todayData?.length && !props.yesterdayData?.length) {
    return null;
  }

  const data = Array.from({ length: 24 }, (_, i) => ({
    hour: i.toString(),
    Today: props.todayData?.find((d) => d.hour === i)?.count || 0,
    Yesterday: props.yesterdayData?.find((d) => d.hour === i)?.count || 0,
  }));

  return {
    data,
    xAxis: { 
      key: "hour", 
      type: "category", 
      title: "Created date - Hour of the Day" 
    },
    yAxis: { title: "" },
    series: [
      { name: "Today", type: "line", color: "#318AD8", showDataPoints: true },
      { name: "Yesterday", type: "line", color: "#A6B1B9", showDataPoints: true },
    ],
    colors: ["#318AD8", "#A6B1B9"],
  };
});

function formatTime(hours: number): string {
  if (!hours || hours === 0) return "0";
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  return `${hours.toFixed(1)}h`;
}
</script>
