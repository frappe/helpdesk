<template>
  <div
    class="flex w-full min-w-0 items-center rounded p-2 text-base font-medium text-gray-800"
    :class="{ 'bg-gray-200': active }"
  >
    <component
      :is="item.icon"
      v-if="item.icon"
      class="mr-3 h-4 w-4 text-gray-700"
    />
    <span class="overflow-hidden text-ellipsis whitespace-nowrap">
      {{ item.title }}&nbsp;
    </span>
    <span
      v-if="item.modified"
      class="ml-auto whitespace-nowrap pl-2 text-gray-600"
    >
      {{ dayjs(item.modified).fromNow(true) }}
    </span>
  </div>
</template>
<script setup lang="ts">
import { dayjs } from "@/dayjs";

defineProps({
  item: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    required: true,
  },
});
</script>
