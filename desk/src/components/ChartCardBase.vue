<template>
  <div
    class="flex flex-col w-full h-full rounded-5 p-4"
    :class="[orientation == 'horizontal' && 'pt-3']"
  >
    <slot name="title">
      <div class="text-ink-gray-5 text-base mb-2">
        {{ title }}
      </div>
    </slot>
    <div
      class="flex flex-col gap-2 h-full w-full"
      v-if="orientation === 'vertical'"
    >
      <div class="flex items-end w-full gap-2">
        <slot name="text">
          <div
            class="text-2xl-medium text-center text-ink-gray-8 whitespace-nowrap"
          >
            {{ text }}
          </div>
        </slot>
        <div v-if="timelineFilter" class="flex items-center text-sm gap-1">
          <div class="flex items-center gap-1" :class="percentageChange.color">
            <span
              v-if="percentageChange.icon"
              :class="percentageChange.icon"
              class="size-4"
            />
            <div>{{ percentageChange.value }}%</div>
          </div>
          <Dropdown :options="durationOptions">
            <div
              class="flex items-center gap-0.5 text-ink-gray-5 hover:text-ink-gray-6 cursor-pointer shrink-0"
            >
              <div class="flex gap-1">
                <span>vs</span>
                <span>{{ __(currentDuration).toLowerCase() }}</span>
              </div>
              <LucideChevronDown class="size-4" />
            </div>
            <template #item-label="{ item }">
              <div
                class="data-[disabled]:cursor-not-allowed group flex w-full items-center rounded-4 px-2 text-base focus:outline-none focus:bg-surface-gray-3 data-[highlighted]:bg-surface-gray-3 data-[state=open]:bg-surface-gray-3 whitespace-nowrap text-ink-gray-7 cursor-pointer justify-between"
              >
                <span>
                  {{ item.label }}
                </span>
              </div>
            </template>
            <template #item-suffix="{ item }">
              <LucideCheck
                v-if="item.label == __(currentDuration)"
                class="size-4"
              />
            </template>
          </Dropdown>
        </div>
      </div>
      <slot name="chart">
        <div v-if="chartConfig" class="w-full h-full">
          <ECharts :options="chartConfig" class="w-full h-full" />
        </div>
      </slot>
    </div>
    <div class="flex flex-col gap-2 h-full w-full" v-else>
      <div class="flex items-end w-full gap-2 justify-between flex-1">
        <slot name="text">
          <span
            class="text-2xl-medium text-center text-ink-gray-8 whitespace-nowrap"
          >
            {{ text }}
          </span>
        </slot>
        <slot name="chart">
          <div v-if="chartConfig" class="h-full max-w-[50%] w-[50%]">
            <ECharts :options="chartConfig" class="w-full h-full" />
          </div>
        </slot>
      </div>
      <div v-if="timelineFilter" class="flex items-center text-sm gap-1">
        <div class="flex items-center gap-1" :class="percentageChange.color">
          <span
            v-if="percentageChange.icon"
            :class="percentageChange.icon"
            class="size-4"
          />
          <div>{{ percentageChange.value }}%</div>
        </div>
        <Dropdown :options="durationOptions">
          <div
            class="flex items-center gap-0.5 text-ink-gray-5 hover:text-ink-gray-6 cursor-pointer shrink-0"
          >
            vs {{ __(currentDuration).toLowerCase() }}
            <LucideChevronDown class="size-4" />
          </div>
          <template #item-label="{ item }">
            <div
              class="data-[disabled]:cursor-not-allowed group flex w-full items-center rounded-4 px-2 text-base focus:outline-none focus:bg-surface-gray-3 data-[highlighted]:bg-surface-gray-3 data-[state=open]:bg-surface-gray-3 whitespace-nowrap text-ink-gray-7 cursor-pointer justify-between"
            >
              <span>
                {{ item.label }}
              </span>
            </div>
          </template>
          <template #item-suffix="{ item }">
            <LucideCheck
              v-if="item.label == __(currentDuration)"
              class="size-4"
            />
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LucideCheck from "~icons/lucide/check";
import LucideChevronDown from "~icons/lucide/chevron-down";
import { __ } from "@/translation";
import { EChartsOption } from "echarts";
import { Dropdown } from "frappe-ui";
import { ECharts } from "frappe-ui/experimental";
import { computed, type PropType } from "vue";

const props = defineProps({
  title: {
    type: String,
  },
  text: {
    type: [Number, String] as PropType<number | string>,
    default: "",
  },
  percentageChange: {
    type: Object,
    required: true,
  },
  chartConfig: {
    type: Object as PropType<EChartsOption>,
    required: true,
  },
  currentDuration: {
    type: String,
    default: __("Last month"),
  },
  orientation: {
    type: String as PropType<"vertical" | "horizontal">,
    default: "vertical",
  },
  timelineFilter: {
    type: Boolean,
    default: true,
  },
});

const chartConfig = computed<EChartsOption>(() => props.chartConfig);

const currentDuration = computed(() => props.currentDuration);

const emit = defineEmits(["changeDuration"]);

// the emitted value is the untranslated key: it travels to the API as the
// period, so only the label goes through __()
const DURATIONS = ["Last week", "Last month", "Last 3 months"];

const durationOptions = DURATIONS.map((duration) => ({
  label: __(duration),
  onClick: () => {
    if (currentDuration.value !== duration) emit("changeDuration", duration);
  },
}));
</script>
