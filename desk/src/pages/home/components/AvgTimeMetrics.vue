<template>
  <div class="flex flex-col rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="flex items-center justify-between">
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __("Average Time Metrics") }}
      </div>
      <TabButtons
        v-if="
          timeAverages.first_response != '0m' || timeAverages.resolution != '0m'
        "
        :buttons="[
          {
            label: '3M',
            value: '3m',
          },
          {
            label: '6M',
            value: '6m',
          },
          {
            label: '1Y',
            value: '1y',
          },
        ]"
        :model-value="currentDuration"
        @update:model-value="onDurationChange"
      />
    </div>
    <div
      v-if="
        timeAverages.first_response == '0m' && timeAverages.resolution == '0m'
      "
      class="flex flex-col justify-center items-center text-center gap-2 h-full w-full"
    >
      <div class="flex flex-col gap-2 max-w-60">
        <div class="text-base font-medium text-ink-gray-7">
          {{ __("No average metrics") }}
        </div>
        <div class="text-base text-ink-gray-6">
          {{ __("Average response and resolution metrics not yet generated") }}
        </div>
      </div>
    </div>
    <div v-else class="flex flex-col mt-5 grow w-full">
      <div class="flex items-center gap-12">
        <div>
          <div class="text-lg font-medium text-ink-gray-8">
            {{ timeAverages.first_response }}
          </div>
          <div class="text-base text-ink-gray-5 flex items-center gap-2 mt-1">
            <div class="size-2 bg-black rounded-full" />
            {{ __("Avg. first response") }}
          </div>
        </div>
        <div>
          <div class="text-lg font-medium text-ink-gray-8">
            {{ timeAverages.resolution }}
          </div>
          <div class="text-base text-ink-gray-5 flex items-center gap-2 mt-1">
            <div class="size-2 bg-gray-400 rounded-full" />
            {{ __("Avg. resolution time") }}
          </div>
        </div>
      </div>
      <div class="w-full grow">
        <EChart :options="chartConfig" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, markRaw, onMounted, ref } from "vue";
import EChart from "./EChart.vue";
import { EChartsOption } from "echarts";
import { createResource, TabButtons } from "frappe-ui";
import { formatTime } from "@/utils";
import { __ } from "@/translation";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const currentDuration = ref("6m");

const getAvgTimeMetricsResource = createResource({
  url: "helpdesk.api.agent_dashboard.get_avg_time_metrics",
  type: "GET",
  makeParams: () => {
    return {
      period: currentDuration.value.toLowerCase(),
    };
  },
});

const timeAverages = computed(() => {
  const _averageFirstResponse = getAvgTimeMetricsResource.fetched
    ? getAvgTimeMetricsResource.data?.averages.first_response
    : props.data?.averages?.first_response || 0;
  const _averageResolution = getAvgTimeMetricsResource.fetched
    ? getAvgTimeMetricsResource.data?.averages.resolution
    : props.data?.averages?.resolution || 0;

  return {
    first_response:
      formatTime(_averageFirstResponse, {
        day: true,
        hour: true,
        minute: true,
      }) || "0m",
    resolution:
      formatTime(_averageResolution, {
        day: true,
        hour: true,
        minute: true,
      }) || "0m",
  };
});

const chartConfig = computed<EChartsOption>(() => {
  let data = getAvgTimeMetricsResource.fetched
    ? getAvgTimeMetricsResource.data?.data
    : props.data?.data || [];

  return {
    legend: {},
    tooltip: {
      trigger: "item",
      borderColor: "#eee",
      borderWidth: 1,
      padding: 10,
      textStyle: {
        color: "#000",
      },
      formatter: (params) => {
        const [category, firstResponse, resolution] = params.data;
        if (params.seriesIndex === 0) {
          return `<b>${category}</b><br/>${__(
            "Avg. First Response"
          )}: <b>${formatTime(firstResponse, {
            day: true,
            hour: true,
            minute: true,
          })}</b>`;
        } else {
          return `<b>${category}</b><br/>${__(
            "Avg. Resolution"
          )}: <b>${formatTime(resolution, {
            day: true,
            hour: true,
            minute: true,
          })}</b>`;
        }
      },
    },
    dataset: {
      source: data,
    },
    xAxis: {
      type: "category",
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      axisLabel: {
        formatter: (value) => {
          if (value < 3600) {
            return (value / 60).toFixed(0) + "m";
          } else if (value < 86400) {
            return (value / 3600).toFixed(0) + "h";
          } else {
            return (value / 86400).toFixed(0) + "d";
          }
        },
        margin: 20,
      },
      axisTick: { show: true },
      splitLine: {
        lineStyle: {
          type: "dashed",
          color: "#ddd",
          width: 0.8,
        },
      },
    },
    series: [
      {
        type: "bar",
        color: "black",
        barWidth: "12%",
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
      {
        type: "bar",
        color: "#E2E2E2",
        barWidth: "12%",
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
    grid: {
      left: 50,
      right: 50,
      top: 30,
      bottom: 30,
    },
  };
});

const onDurationChange = (duration: string) => {
  currentDuration.value = duration;
  getAvgTimeMetricsResource.submit();
};

onMounted(() => {
  if (!props.data?.data) {
    getAvgTimeMetricsResource.submit();
  }
});
</script>
