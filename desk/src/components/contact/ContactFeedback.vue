<template>
  <div>
    <!-- Heading -->
    <h3 class="font-semibold text-lg mt-2.5 mb-4">Feedback</h3>
    <section class="flex items-start gap-6">
      <!-- Left: Feedback summary card (sticky) -->
      <FeedbackCard :count="count" />

      <!-- Right: User reviews list -->
      <FeedbackList :feedbackResource="feedbackResource" :count="count" />
    </section>
  </div>
</template>

<script setup lang="ts">
import type { ListResource } from "@/types";
import type { HDTicket } from "@/types/doctypes";
import FeedbackCard from "./FeedbackCard.vue";
import FeedbackList from "./FeedbackList.vue";

const props = defineProps<{
  name: string;
  feedbackResource: ListResource<HDTicket>;
  count: number;
}>();
</script>

<style scoped></style>
