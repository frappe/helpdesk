<template>
  <div class="flex flex-col rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="flex items-center justify-between">
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __("Average Time Metrics") }}
      </div>
      <div class="flex items-center gap-2">
        <Dropdown
          v-if="currentDuration !== 'custom_range'"
          :options="durationOptions"
          placement="right"
        >
          <template #default>
            <Button :label="currentDurationLabel" icon-right="chevron-down" />
          </template>
          <template #item-label="{ item }">
            <span>
              {{ item.label }}
            </span>
          </template>

          <template #item-suffix="{ item }">
            <FeatherIcon
              v-if="item.label == durationLabels[currentDuration]"
              name="check"
              class="size-4"
            />
          </template>
        </Dropdown>
        <DateRangePicker
          v-else
          ref="datePickerRef"
          v-model="customDateRange"
          :placeholder="__('Select range')"
          @update:model-value="onCustomRangeSelected"
          :format="'MMM D'"
          @click="datePickerRef?.open()"
          placement="bottom-end"
          class="!w-48"
        />
      </div>
    </div>
    <div
      v-if="
        timeAverages.first_response == '0m' && timeAverages.resolution == '0m'
      "
      class="relative flex flex-col mt-5 grow w-full select-none"
    >
      <div class="flex items-center gap-12">
        <div>
          <div
            class="text-lg font-medium text-ink-gray-8 w-20 rounded-sm h-4 bg-surface-gray-1"
          />
          <div
            class="w-40 rounded-sm h-4 bg-surface-gray-1 text-base flex items-center gap-2 mt-1"
          />
        </div>
        <div>
          <div
            class="text-lg font-medium text-ink-gray-8 w-20 rounded-sm h-4 bg-surface-gray-1"
          />
          <div
            class="w-40 rounded-sm h-4 bg-surface-gray-1 text-base flex items-center gap-2 mt-1"
          />
        </div>
      </div>
      <div class="w-full grow pointer-events-none mt-6 relative flex flex-col">
        <div class="flex-1 relative flex items-end justify-around px-4">
          <div class="absolute inset-0 flex flex-col justify-between z-0">
            <div
              v-for="idx in 5"
              :key="idx"
              class="border-t border-dashed border-surface-gray-2 w-full"
            />
          </div>
          <div
            v-for="idx in 6"
            :key="idx"
            class="relative z-10 flex gap-2 h-full items-end pb-0"
          >
            <div
              class="w-[12px] bg-surface-gray-2 rounded-t-sm"
              :style="{ height: [20, 20, 30, 15, 10, 10][idx - 1] + '%' }"
            />
            <div
              class="w-[12px] bg-surface-gray-2 rounded-t-sm"
              :style="{ height: [60, 55, 85, 45, 30, 20][idx - 1] + '%' }"
            />
          </div>
        </div>
        <div class="flex justify-around mt-3 mb-2 px-6">
          <div
            class="w-6 h-2 bg-surface-gray-2 rounded"
            v-for="i in 6"
            :key="i"
          />
        </div>
      </div>
      <EmptyState
        class="absolute inset-0 z-10"
        :title="__('No average metrics')"
        :description="
          __('Average response and resolution metrics not available')
        "
        variant="overlay"
        text="md"
      />
    </div>
    <div v-else class="flex flex-col mt-5 grow w-full">
      <div class="flex items-center gap-12">
        <div>
          <div class="text-lg font-medium text-ink-gray-8">
            {{ timeAverages.first_response }}
          </div>
          <div class="text-base text-ink-gray-5 flex items-center gap-2 mt-1">
            <div class="size-2 bg-black rounded-full" />
            {{ __("Avg. first response time") }}
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
        <ECharts :options="chartConfig" class="w-full h-full" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, type PropType, nextTick } from "vue";
import { EChartsOption } from "echarts";
import {
  createResource,
  Dropdown,
  DateRangePicker,
  Button,
  FeatherIcon,
  ECharts,
} from "frappe-ui";
import { formatTime } from "@/utils";
import { __ } from "@/translation";
import EmptyState from "@/components/EmptyState.vue";

type MetricsData = {
  averages: {
    first_response: number;
    resolution: number;
  };
  data: [string, number, number][];
};

const props = defineProps({
  data: {
    type: Object as PropType<MetricsData>,
    required: true,
  },
});

const currentDuration = ref("6m");
const datePickerRef = ref<{ open: () => void } | null>(null);
const customDateRange = ref<string | undefined>(undefined);

const durationLabels: Record<string, string> = {
  "3m": __("3 Months"),
  "6m": __("6 Months"),
  "1y": __("1 Year"),
  custom_range: __("Custom Range"),
};

const currentDurationLabel = computed(() => {
  return durationLabels[currentDuration.value] || __("6 Months");
});

const durationOptions = computed(() => [
  {
    label: __("3 Months"),
    onClick: () => onDurationChange("3m"),
  },
  {
    label: __("6 Months"),
    onClick: () => onDurationChange("6m"),
  },
  {
    label: __("1 Year"),
    onClick: () => onDurationChange("1y"),
  },
  {
    label: __("Custom Range"),
    onClick: () => {
      currentDuration.value = "custom_range";
      nextTick(() => {
        datePickerRef.value?.open();
      });
    },
  },
]);

const onCustomRangeSelected = (range: string) => {
  if (!range) {
    currentDuration.value = "6m";
    customDateRange.value = undefined;
    getAvgTimeMetricsResource.submit();
    return;
  }
  currentDuration.value = "custom_range";
  customDateRange.value = range;
  getAvgTimeMetricsResource.submit();
};

const getAvgTimeMetricsResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_avg_time_metrics",
  type: "GET",
  makeParams: () => {
    const params: Record<string, string> = {
      period: currentDuration.value.toLowerCase(),
    };
    if (currentDuration.value === "custom_range" && customDateRange.value) {
      const [from, to] = customDateRange.value.split(",");
      params.from_date = from;
      params.to_date = to;
    }
    return params;
  },
});

const timeAverages = computed(() => {
  const _data = getAvgTimeMetricsResource.fetched
    ? getAvgTimeMetricsResource.data
    : props.data;
  const _averageFirstResponse = _data?.averages?.first_response || 0;
  const _averageResolution = _data?.averages?.resolution || 0;

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
        const p = params as unknown as {
          data: [string, number, number];
          seriesIndex: number;
        };
        const [category, firstResponse, resolution] = p.data;
        if (p.seriesIndex === 0) {
          return `<span>${category}</span><br/>${__(
            "Avg. first response time"
          )}: <b>${formatTime(firstResponse, {
            day: true,
            hour: true,
            minute: true,
          })}</b>`;
        } else {
          return `<span>${category}</span><br/>${__(
            "Avg. resolution time"
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
        formatter: (value: number) => {
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
  if (currentDuration.value === duration) return;
  customDateRange.value = undefined;
  currentDuration.value = duration;
  getAvgTimeMetricsResource.submit();
};

onMounted(() => {
  if (!props.data?.data) {
    getAvgTimeMetricsResource.submit();
  }
});
</script>
