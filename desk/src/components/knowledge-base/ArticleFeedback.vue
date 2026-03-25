<template>
  <div class="flex items-center justify-between mb-8 p-4 rounded-lg bg-gray-50">
    <!-- Feedback Section -->
    <div>
      <!-- was this article helpful? -->
      <div class="flex flex-col gap-2">
        <span class="text-gray-800 text-sm !text-[14px]">{{
          __("Was this article Helpful?")
        }}</span>

        <div class="flex gap-1 text-gray-600">
          <span class="text-sm">
            {{ __("If your issue isn't resolved, raise a support ticket") }}
          </span>
          <router-link :to="{ name: 'TicketNew' }">
            <p class="underline font-base text-sm">here</p>
          </router-link>
        </div>
      </div>
    </div>
    <!-- Create a ticket CTA -->
    <div class="flex items-center justify-center gap-2">
      <div class="flex items-center gap-1">
        <component
          :is="_feedback === 1 ? ThumbsUpFilledIcon : ThumbsUpIcon"
          class="w-4 h-4 m-1.5 cursor-pointer"
          @click="handleFeedbackClick(1)"
        />
        <component
          :is="_feedback === 2 ? ThumbsDownFilledIcon : ThumbsDownIcon"
          class="w-4 h-4 m-1.5 cursor-pointer"
          @click="handleFeedbackClick(2)"
        />
      </div>
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
import { toast } from "frappe-ui";
import { __ } from "@/translation";

interface P {
  feedback: FeedbackAction;
  articleId: string;
}

const props = withDefaults(defineProps<P>(), {
  feedback: 0,
});

const _feedback = ref(props.feedback);
const emit = defineEmits(["articleReaction"]);

function handleFeedbackClick(action: FeedbackAction) {
  if (action === _feedback.value) {
    return;
  }
  _feedback.value = action;
  setFeedback.submit(
    { articleId: props.articleId, action },
    {
      onSuccess: () => {
        emit("articleReaction", _feedback.value);
        if (_feedback.value === 0) {
          return;
        }
        toast.success(__("Feedback submitted successfully."));
      },
    }
  );
}
</script>

<style scoped></style>
