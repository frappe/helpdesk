<template>
  <div class="w-full p-4 rounded" :class="styles[0]">
    <!-- Header -->
    <div class="flex gap-[9px] mb-1.5 items-center">
      <p class="text-base text-ink-gray-8 font-medium">
        {{ activity.feedback }}
      </p>
      <StarRating :rating="activity.feedback_rating" />
    </div>
    <!-- Optional Text -->
    <div v-if="activity.feedback_extra">
      <p class="mt-2 text-sm text-gray-700">{{ activity.feedback_extra }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FeedbackActivity } from "@/types";
import { computed, PropType } from "vue";
import StarRating from "../StarRating.vue";

const props = defineProps({
  activity: {
    type: Object as PropType<FeedbackActivity>,
    required: true,
  },
});

const styles = computed(() => {
  if (props.activity.feedback_rating <= 0.4) return ["bg-surface-red-1", "red"];
  if (props.activity.feedback_rating <= 0.6)
    return ["bg-surface-amber-1", "yellow"];
  return ["bg-surface-green-1", "yellow"];
});
</script>
