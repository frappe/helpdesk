<template>
  <div>
    <div class="flex">
      <div class="min-w-[106px] pb-1.5">Rating</div>
      <div class="px-1.5">
        <StarRating :rating="ticket.feedback_rating" />
      </div>
    </div>
    <div class="flex">
      <div class="w-[106px] pb-1.5">Feedback</div>
      <div class="px-1.5 text-gray-800">
        {{ ticket.feedback_text }}
      </div>
    </div>
    <div v-if="ticket.feedback_extra" class="flex">
      <div class="min-w-[106px] pb-1.5">Comment</div>
      <div class="px-1.5 text-gray-800">
        {{ ticket.feedback_extra }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StarRating from "../StarRating.vue";

defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped></style>
