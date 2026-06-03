<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <LoadingIndicator :scale="10" />
    </div>

    <!-- Empty -->
    <div
      v-else-if="!feedbackCount.data"
      class="flex flex-col items-center justify-center gap-3 py-16 text-center"
    >
      <LucideStar class="h-7.5 w-7.5 text-ink-gray-4" />
      <div class="flex flex-col gap-1 max-w-[282px] m-auto">
        <p class="text-base font-medium text-ink-gray-7">
          {{ __("No feedback yet") }}
        </p>
        <p class="text-ink-gray-6 text-base">
          {{
            __("Feedback from this contact will appear here once available.")
          }}
        </p>
      </div>
    </div>

    <!-- Content -->
    <section v-else class="flex items-start gap-6">
      <FeedbackList :name="name" />
      <FeedbackCard :name="name" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { useContactFeedback } from "@/composables/contact";
import { __ } from "@/translation";
import { LoadingIndicator } from "frappe-ui";
import LucideStar from "~icons/lucide/star";
import FeedbackCard from "./FeedbackCard.vue";
import FeedbackList from "./FeedbackList.vue";

const props = defineProps<{
  name: string;
}>();

const { feedbackCount, loading } = useContactFeedback(props.name);
</script>
