<template>
  <div>
    <!-- Heading -->
    <h3 class="font-semibold text-lg mt-2.5 mb-4">Feedback</h3>
    <section class="flex items-start gap-6">
      <!-- Left: Feedback summary card (sticky) -->
      <FeedbackCard :name="name" />

      <!-- Right: User reviews list -->
      <FeedbackList :name="name" />
    </section>
  </div>
</template>

<script setup lang="ts">
import FeedbackCard from "./FeedbackCard.vue";
import FeedbackList from "./FeedbackList.vue";

defineProps<{
  name: string;
}>();
</script>

<style scoped></style>
