<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4">
    <div class="flex justify-between items-center mb-4">
      <div>
        <h3 class="text-base font-medium text-gray-900">Customer satisfaction</h3>
        <p class="text-xs text-gray-500">Across helpdesk this month</p>
      </div>
      <button
        class="text-sm text-blue-600 hover:text-blue-700"
        @click="handleViewDetails"
      >
        View details
      </button>
    </div>

    <div v-if="responsesReceived > 0" class="grid grid-cols-2 gap-4">
      <div class="flex flex-col">
        <span class="text-xs text-gray-500">Responses received</span>
        <span class="text-xl font-semibold text-gray-900">{{ responsesReceived }}</span>
      </div>
      <div class="flex flex-col">
        <span class="text-xs text-gray-500">Positive</span>
        <div class="flex items-center gap-2">
          <span class="text-xl font-semibold text-green-500">{{ positive }}%</span>
          <span class="text-lg">😊</span>
        </div>
      </div>
      <div class="flex flex-col">
        <span class="text-xs text-gray-500">Neutral</span>
        <div class="flex items-center gap-2">
          <span class="text-xl font-semibold text-yellow-500">{{ neutral }}%</span>
          <span class="text-lg">😐</span>
        </div>
      </div>
      <div class="flex flex-col">
        <span class="text-xs text-gray-500">Negative</span>
        <div class="flex items-center gap-2">
          <span class="text-xl font-semibold text-red-500">{{ negative }}%</span>
          <span class="text-lg">😞</span>
        </div>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-8 text-gray-400">
      <LucideMessageSquare class="w-8 h-8 mb-2" />
      <span class="text-sm">No feedback received this period</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import LucideMessageSquare from "~icons/lucide/message-square";

interface Props {
  responsesReceived: number;
  positive: number;
  neutral: number;
  negative: number;
}

defineProps<Props>();

const router = useRouter();

function handleViewDetails() {
  router.push({
    name: "TicketsAgent",
    query: { has_feedback: "1" },
  });
}
</script>
