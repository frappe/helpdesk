<template>
  <div class="flex flex-col rounded-md p-4 grow w-full h-full overflow-hidden">
    <div class="flex items-center justify-between">
      <div class="text-lg font-semibold text-ink-gray-8">
        {{ __("Average Time Metrics") }}
      </div>
      <div class="flex items-center gap-2">
        <Dropdown
          v-if="!showDatePicker && currentDuration !== 'custom_range'"
          :options="durationOptions"
          placement="right"
        >
          <template #default>
            <Button :label="currentDurationLabel" icon-right="chevron-down" />
          </template>
          <template #item="{ item }">
            <div
              class="data-[disabled]:cursor-not-allowed group flex h-7 w-full items-center rounded px-2 text-base focus:outline-none focus:bg-surface-gray-3 data-[highlighted]:bg-surface-gray-3 data-[state=open]:bg-surface-gray-3 whitespace-nowrap text-ink-gray-7 cursor-pointer justify-between"
            >
              <span>
                {{ item.label }}
              </span>
              <FeatherIcon
                v-if="item.label == durationLabels[currentDuration]"
                name="check"
                class="size-4"
              />
            </div>
          </template>
        </Dropdown>
        <DateRangePicker
          v-else
          ref="datePickerRef"
          v-model="customDateRange"
          :placeholder="__('Select range')"
          @update:model-value="onCustomRangeSelected"
          :formatter="formatDateRange"
          @click="datePickerRef?.open()"
          placement="bottom-end"
          class="w-[228px]"
        />
      </div>
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
          {{ __("Average response and resolution metrics not available") }}
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
const showDatePicker = ref(false);
const datePickerRef = ref<{ open: () => void } | null>(null);
const customDateRange = ref<string | undefined>(undefined);

const durationLabels: Record<string, string> = {
  "3m": __("3 Months"),
  "6m": __("6 Months"),
  "1y": __("1 Year"),
  custom_range: __("Custom Range"),
};

const currentDurationLabel = computed(() => {
  if (currentDuration.value === "custom_range" && customDateRange.value) {
    const [from, to] = customDateRange.value.split(",");
    return `${formatDateRange(from)} – ${formatDateRange(to)}`;
  }
  return durationLabels[currentDuration.value] || __("6 Months");
});

function formatDateRange(date: string) {
  const d = new Date(date);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: d.getFullYear() === new Date().getFullYear() ? undefined : "numeric",
  });
}

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
      showDatePicker.value = true;
      nextTick(() => {
        datePickerRef.value?.open();
      });
    },
  },
]);

const onCustomRangeSelected = (range: string) => {
  if (!range) {
    showDatePicker.value = false;
    currentDuration.value = "6m";
    customDateRange.value = undefined;
    getAvgTimeMetricsResource.submit();
    return;
  }
  showDatePicker.value = false;
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
  showDatePicker.value = false;
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
