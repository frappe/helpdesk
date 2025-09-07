<template>
  <div class="w-full p-4 rounded bg-surface-green-1">
    <!-- Header -->
    <div class="mb-4.5">
      <div class="flex gap-[9px] mb-1.5 items-center">
        <p class="text-base text-ink-gray-8 font-medium">
          {{ activity.feedback }}
        </p>
        <StarRating :rating="activity.feedback_rating" :read-only="true" />
      </div>
      <!-- Optional Text -->
      <div v-if="activity.feedback_extra">
        <p class="mt-2 text-sm text-gray-700">{{ activity.feedback_extra }}</p>
      </div>
    </div>
    <!-- Footer with contact info and time -->
    <div>
      <p class="text-ink-gray-8 text-base">{{ activity.sender.name }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FeedbackActivity } from "@/types";
import { PropType } from "vue";
import StarRating from "../StarRating.vue";

defineProps({
  activity: {
    type: Object as PropType<FeedbackActivity>,
    required: true,
  },
});
</script>
