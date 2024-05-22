<template>
  <div class="flex-col text-base">
    <div class="mb-0.5 flex justify-between py-1.5">
      <div class="text-gray-600">
        <span class="font-medium text-gray-800">
          {{ commenter }}
        </span>
        <span> added a</span>
        <span class="max-w-xs truncate font-medium text-gray-800">
          comment
        </span>
      </div>
      <div>
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <div class="text-gray-600">
            {{ timeAgo(creation) }}
          </div>
        </Tooltip>
      </div>
    </div>
    <div
      class="prose-f grow cursor-pointer rounded bg-gray-50 px-4 py-3 text-base leading-6 transition-all duration-300 ease-in-out"
      v-html="content"
    />
  </div>
</template>

<script setup lang="ts">
import { dateFormat, timeAgo, dateTooltipFormat } from "@/utils";
const props = defineProps({
  creation: {
    type: String,
    required: true,
  },
  content: {
    type: String,
    required: true,
  },
  commenter: {
    type: String,
    required: true,
  },
});
</script>
