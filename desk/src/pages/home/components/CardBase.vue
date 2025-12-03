<template>
  <div class="flex flex-col w-full h-full rounded-md p-4">
    <slot name="title">
      <div class="text-ink-gray-5 text-base mb-2">
        {{ title }}
      </div>
    </slot>
    <div class="flex flex-col gap-2 h-full w-full">
      <slot name="body">
        <div class="flex items-end w-full h-full gap-2">
          <div
            class="text-2xl font-medium text-center text-ink-gray-8 whitespace-nowrap"
          >
            {{ text }}
          </div>
          <slot name="chart">
            <div v-if="props.chartConfig" class="w-full h-full">
              <EChart :options="chartConfig" />
            </div>
          </slot>
        </div>
      </slot>
      <slot v-if="!hideCardBottom" name="card-bottom">
        <div class="flex items-center text-sm gap-1">
          <div class="flex items-center gap-1" :class="percentageChange.color">
            <FeatherIcon :name="percentageChange.icon" class="size-4" />
            <div>{{ percentageChange.value }}%</div>
          </div>
          <Dropdown :options="durationOptions">
            <div
              class="flex items-center gap-0.5 text-ink-gray-5 hover:text-ink-gray-6 cursor-pointer"
            >
              vs {{ currentDuration.toLowerCase() }}
              <FeatherIcon name="chevron-down" class="size-4" />
            </div>
          </Dropdown>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from "vue";
import EChart from "./EChart.vue";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { __ } from "@/translation";

const props = defineProps({
  title: {
    type: String,
  },
  text: {
    type: [Number, String] as PropType<number | string>,
    default: "",
  },
  chartConfig: {
    type: Object,
  },
  currentDuration: {
    type: String,
    default: "Last month",
  },
  percentageChange: {
    type: Object,
  },
  hideCardBottom: {
    type: Boolean,
    default: false,
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
</script>
