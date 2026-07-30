<template>
  <Section :label="__('Feedback')" v-model:opened="opened">
    <!-- Comment reads as a quote, the preset splits into pills on commas -->
    <div class="flex flex-col items-start gap-3 pb-4 pt-0.5">
      <StarRating :rating="rating" :aria-label="`${rating * 5} out of 5`" />
      <div v-if="comment">
        <p
          ref="commentRef"
          class="whitespace-pre-line text-p-base text-ink-gray-7"
          :class="!showFullComment && 'line-clamp-3'"
        >
          <span class="text-ink-gray-4">&ldquo;</span>{{ comment
          }}<span class="text-ink-gray-4">&rdquo;</span>
        </p>
        <button
          v-if="isCommentClamped || showFullComment"
          class="mt-0.5 text-base text-ink-gray-5 hover:text-ink-gray-7"
          @click="showFullComment = !showFullComment"
        >
          {{ showFullComment ? __("Show less") : __("Show more") }}
        </button>
      </div>
      <div v-if="presetChips.length" class="flex flex-wrap gap-1.5">
        <span
          v-for="chip in presetChips"
          :key="chip"
          class="rounded-full border px-2.5 py-1 text-base leading-4 text-ink-gray-7"
        >
          {{ chip }}
        </span>
      </div>
    </div>
  </Section>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { useResizeObserver } from "@vueuse/core";
import { computed, ref } from "vue";
import Section from "../Section.vue";
import StarRating from "../StarRating.vue";

const props = defineProps<{
  rating: number;
  feedback?: string;
  comment?: string;
}>();

const opened = defineModel<boolean>("opened", { default: true });

// the preset reads as tags ("Adequate help, bit slow"), so split it on commas
const presetChips = computed(() =>
  (props.feedback ?? "")
    .split(",")
    .map((part: string) => part.trim())
    .filter(Boolean)
    .map((part: string) => part.charAt(0).toUpperCase() + part.slice(1))
);

const commentRef = ref<HTMLElement | null>(null);
const showFullComment = ref(false);
const isCommentClamped = ref(false);

// The sidebar is resizable, so how many lines the comment takes changes with
// the column width, not just with the text.
useResizeObserver(commentRef, () => {
  const element = commentRef.value;
  if (!element || showFullComment.value) return;
  isCommentClamped.value = element.scrollHeight > element.clientHeight + 1;
});
</script>
