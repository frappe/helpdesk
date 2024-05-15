<template>
  <div class="mt-1.5 flex justify-between text-base">
    <div class="text-gray-600">
      <span class="font-medium text-gray-800">
        {{ user }}
      </span>
      <span> {{ content }}</span>
    </div>
    <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
      <div class="text-gray-600">
        {{ timeAgo(creation) }}
      </div>
    </Tooltip>
  </div>
  <div v-if="show_others">
    <div
      v-for="relatedActivity in relatedActivities"
      :key="relatedActivity.creation"
      class="mt-2 flex justify-between text-base"
    >
      <div class="text-gray-600">
        <span class="font-medium text-gray-800">
          {{ relatedActivity.user }}
        </span>
        <span> {{ relatedActivity.content }}</span>
      </div>
      <Tooltip :text="dateFormat(relatedActivity.creation, dateTooltipFormat)">
        <div class="text-gray-600">
          {{ timeAgo(relatedActivity.creation) }}
        </div>
      </Tooltip>
    </div>
  </div>
  <Button
    v-if="relatedActivities.length"
    :label="
      show_others ? 'Hide' : `${relatedActivities.length} other activities`
    "
    variant="outline"
    class="mt-2"
    @click="show_others = !show_others"
  >
    <template #suffix>
      <FeatherIcon
        :name="show_others ? 'chevron-up' : 'chevron-down'"
        class="h-4 text-gray-600"
      />
    </template>
  </Button>
</template>

<script setup lang="ts">
import { ref } from "vue";
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
  relatedActivities: {
    type: Array,
    default: () => [],
  },
});

let show_others = ref(false);
</script>
