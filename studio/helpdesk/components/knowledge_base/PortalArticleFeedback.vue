<template>
  <div
    class="flex w-full items-center justify-between gap-4 border-t border-outline-gray-1 pt-6"
  >
    <div class="flex min-w-0 flex-col gap-1.5">
      <span class="text-base text-ink-gray-8">
        {{ __("Was this article helpful?") }}
      </span>
      <span v-if="canRaiseTicket" class="text-p-base text-ink-gray-5">
        {{ __("If your issue isn't resolved, raise a support ticket") }}
        <RouterLink
          :to="ROUTES.newTicket"
          class="text-ink-gray-5 underline underline-offset-2 hover:text-ink-gray-8"
        >
          {{ __("here") }}
        </RouterLink>
      </span>
    </div>
    <div class="-mr-1.5 flex shrink-0 gap-1">
      <Button
        v-for="answer in ANSWERS"
        :key="answer.value"
        variant="ghost"
        :label="answer.label"
        :aria-pressed="feedback === answer.value"
        @click="onFeedback?.(feedback === answer.value ? 0 : answer.value)"
      >
        <template #icon>
          <PortalFeedbackThumb
            :answer="answer.value"
            :filled="feedback === answer.value"
            background="var(--surface-base)"
            class="size-4 text-ink-gray-8"
          />
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import { Button } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import PortalFeedbackThumb from "@app/components/knowledge_base/PortalFeedbackThumb.vue";
import { ROUTES } from "@app/routes";

// Values match HD Article Feedback: 1 like, 2 dislike; 0 clears, sent by a second click.
const ANSWERS = [
  { value: 1, label: __("Yes, it was helpful") },
  { value: 2, label: __("No, it wasn't helpful") },
];

defineProps<{
  feedback?: number;
  onFeedback?: (value: number) => void;
  canRaiseTicket?: boolean;
}>();
</script>
