<template>
  <div
    class="flex w-full min-w-0 items-center rounded p-2 text-base-medium text-ink-gray-8"
    :class="{ 'bg-surface-gray-3': active }"
  >
    <component
      :is="item.icon"
      v-if="item.icon"
      class="me-3 h-4 w-4 text-ink-gray-6"
    />
    <span class="overflow-hidden text-ellipsis whitespace-nowrap">
      {{ __(item.title) }}&nbsp;
    </span>
    <span
      v-if="item.modified"
      class="ms-auto whitespace-nowrap ps-2 text-ink-gray-5"
    >
      {{ dayjs(item.modified).fromNow(true) }}
    </span>
  </div>
</template>
<script setup lang="ts">
import { dayjs } from "frappe-ui";

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
