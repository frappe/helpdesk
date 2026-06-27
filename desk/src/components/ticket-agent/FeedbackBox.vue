<template>
  <div class="w-full p-4 rounded-md" :class="styles[0]">
    <!-- Header -->
    <div
      class="flex mb-1.5 items-center"
      :class="activity.feedback && 'gap-[9px]'"
    >
      <p class="text-base-medium text-ink-gray-8">
        {{ activity.feedback }}
      </p>
      <Rating
        :max="5"
        size="sm"
        disabled
        :model-value="activity.feedback_rating * 5"
      />
    </div>
    <!-- Optional Text -->
    <div v-if="activity.feedback_extra">
      <p class="mt-2 text-p-sm text-ink-gray-7">
        {{ activity.feedback_extra }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FeedbackActivity } from "@/types";
import { Rating } from "frappe-ui";
import { computed, PropType } from "vue";

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
