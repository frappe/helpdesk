<template>
  <div class="flex w-full justify-between text-base">
    <div class="text-gray-600">
      <span class="font-medium text-gray-800">
        {{ user }}
      </span>
      <span> {{ content }}</span>
    </div>
    <Tooltip
      :text="dateFormat(creation, dateTooltipFormat)"
      class="text-gray-600"
    >
      {{ timeAgo(creation) }}
    </Tooltip>
  </div>
</template>

<script setup lang="ts">
import { dateFormat, timeAgo, dateTooltipFormat } from "@/utils";
const props = defineProps({
  user: {
    type: String,
    required: true,
  },
  content: {
    type: String,
    required: true,
  },
  creation: {
    type: String,
    required: true,
  },
});
</script>
