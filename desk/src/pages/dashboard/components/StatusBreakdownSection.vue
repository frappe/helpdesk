<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4 h-full">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-base font-medium text-gray-900">Status breakdown</h3>
        <p class="text-xs text-gray-500">Across helpdesk</p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-60">
      <Button :loading="true" size="lg" variant="ghost" />
    </div>
    <div
      v-else-if="!breakdown || breakdown.total === 0"
      class="flex flex-col items-center justify-center h-60 text-gray-400"
    >
      <LucidePieChart class="w-10 h-10 mb-2" />
      <span class="text-sm">No ticket data for this selection</span>
    </div>
    <div class="flex justify-center items-center py-4">
      <div class="h-72 w-full max-w-[320px]">
        <DonutChart v-if="chartConfig" :config="chartConfig" class="h-full w-full" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, DonutChart } from "frappe-ui";
import { computed } from "vue";
import LucidePieChart from "~icons/lucide/pie-chart";

type StatusBreakdown = {
  open: number;
  resolved: number;
  overdue: number;
  total: number;
};

const props = defineProps<{
  breakdown: StatusBreakdown | null;
  loading: boolean;
}>();

const chartConfig = computed(() => {
  if (!props.breakdown || props.breakdown.total === 0) {
    return null;
  }

  return {
    title: "",
    subtitle: "",
    data: [
      { label: "Open", value: props.breakdown.open },
      { label: "Resolved", value: props.breakdown.resolved },
      { label: "Overdue", value: props.breakdown.overdue },
    ],
    categoryColumn: "label",
    valueColumn: "value",
    colors: ["#318AD8","#F56565","#48BB78"],
    showInlineLabels: false,
  };
});
</script>

