<template>
  <div class="flex items-center justify-between mb-8 p-4 rounded-lg bg-gray-50">
    <!-- Feedback Section -->
    <div>
      <!-- was this article helpful? -->
      <div class="flex items-center gap-2">
        <span class="text-gray-800 text-sm"
          >Did this article solve your issue?</span
        >
        <div class="flex items-center gap-1">
          <component
            :is="_feedback === 1 ? ThumbsUpFilledIcon : ThumbsUpIcon"
            class="w-4 h-4 cursor-pointer"
            @click="handleFeedbackClick(1)"
          />
          <component
            :is="_feedback === 2 ? ThumbsDownFilledIcon : ThumbsDownIcon"
            class="w-4 h-4 cursor-pointer"
            @click="handleFeedbackClick(2)"
          />
        </div>
      </div>
    </div>
    <!-- Create a ticket CTA -->
    <div class="flex items-center justify-center gap-2">
      <span class="font-normal text-sm">
        Can’t find what you’re looking for?
      </span>
      <router-link :to="{ name: 'TicketNew' }">
        <p class="underline font-base text-sm">Create a ticket &rightarrow;</p>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FeedbackAction } from "@/types";
import {
  ThumbsUpIcon,
  ThumbsUpFilledIcon,
  ThumbsDownIcon,
  ThumbsDownFilledIcon,
} from "@/components/icons";
import { setFeedback } from "@/stores/knowledgeBase";
import { ref } from "vue";

interface P {
  feedback: FeedbackAction;
  articleId: string;
}

const props = withDefaults(defineProps<P>(), {
  feedback: 0,
});

const _feedback = ref(props.feedback);

function handleFeedbackClick(action: FeedbackAction) {
  _feedback.value = action;
  if (action === props.feedback) return;
  setFeedback.submit({ articleId: props.articleId, action });
}
</script>

<style scoped></style>
