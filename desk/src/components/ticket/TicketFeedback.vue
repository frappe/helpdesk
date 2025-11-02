<template>
  <div class="flex flex-col gap-4 border-b px-5 pb-3">
    <div class="flex items-start text-base leading-5">
      <div class="min-w-[126px] text-sm">Rating</div>
      <div class="">
        <StarRating :rating="ticket.feedback_rating" />
      </div>
    </div>
    <div class="flex items-start text-base leading-5" v-if="ticket.feedback">
      <div class="min-w-[126px] text-sm">Feedback</div>
      <div class="text-gray-800">
        {{ ticket.feedback }}
      </div>
    </div>
    <div
      v-if="ticket.feedback_extra"
      class="flex items-start text-base leading-5"
    >
      <div class="min-w-[126px] text-sm">Comment</div>
      <div class="text-gray-800">
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
