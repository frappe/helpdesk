<template>
  <div class="flex flex-col w-full h-full rounded-md p-4">
    <slot name="title">
      <div class="text-ink-gray-5 text-base mb-2">
        {{ title }}
      </div>
    </slot>
    <div class="flex flex-col gap-2 h-full w-full">
      <div class="flex items-end w-full gap-2">
        <div
          class="text-2xl font-medium text-center text-ink-gray-8 whitespace-nowrap"
        >
          {{ text }}
        </div>
        <div class="flex items-center text-sm gap-1">
          <div class="flex items-center gap-1" :class="percentageChange.color">
            <FeatherIcon :name="percentageChange.icon" class="size-4" />
            <div>{{ percentageChange.value }}%</div>
          </div>
          <Dropdown :options="durationOptions">
            <div
              class="flex items-center gap-0.5 text-ink-gray-5 hover:text-ink-gray-6 cursor-pointer shrink-0"
            >
              vs {{ currentDuration.toLowerCase() }}
              <FeatherIcon name="chevron-down" class="size-4" />
            </div>
          </Dropdown>
        </div>
      </div>
      <slot name="chart">
        <div v-if="chartConfig" class="w-full h-full">
          <ECharts :options="chartConfig" class="w-full h-full" />
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from "vue";
import { Dropdown, FeatherIcon, ECharts } from "frappe-ui";
import { __ } from "@/translation";
import { EChartsOption } from "echarts";

const props = defineProps({
  title: {
    type: String,
  },
  text: {
    type: [Number, String] as PropType<number | string>,
    default: "",
  },
  chartData: {
    type: Array as PropType<number[]>,
    required: true,
  },
  chartDates: {
    type: Array as PropType<string[]>,
  },
  currentDuration: {
    type: String,
    default: "Last month",
  },
  chartColor: {
    type: Object,
    required: true,
  },
  percentageChange: {
    type: Object,
    required: true,
  },
});

const currentDuration = computed(() => props.currentDuration);

const emit = defineEmits(["changeDuration"]);

const durationOptions = computed(() => {
  const options = [
    {
      label: __("Last week"),
      onClick: () => emit("changeDuration", "Last week"),
    },
    {
      label: __("Last month"),
      onClick: () => emit("changeDuration", "Last month"),
    },
    {
      label: __("Last 3 months"),
      onClick: () => emit("changeDuration", "Last 3 months"),
    },
  ];

  return options.filter((option) => option.label !== currentDuration.value);
});

const chartConfig = computed<EChartsOption>(() => {
  const color = props.chartColor.lineColor;
  const gradientColor = props.chartColor.gradientColor;
  return {
    xAxis: {
      type: "category",
      data: props.chartDates,
      show: false,
      boundaryGap: false,
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        data: props.chartData,
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
</script>
