<template>
  <div
    class="flex w-full items-center justify-between gap-4 rounded-[12px] bg-surface-gray-1 px-4 py-4"
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
    <div class="flex shrink-0 gap-1">
      <Button
        v-for="answer in ANSWERS"
        :key="answer.value"
        variant="ghost"
        :label="answer.label"
        :aria-pressed="vote === answer.value"
        @click="onVote?.(vote === answer.value ? '0' : answer.value)"
      >
        <template #icon>
          <!-- Inline, not a lucide class: the chosen answer's thumb fills, which a mask icon cannot. -->
          <svg
            viewBox="0 0 24 24"
            class="size-4 text-ink-gray-8"
            :fill="vote === answer.value ? 'currentColor' : 'none'"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path :d="answer.thumb" />
            <!-- The cuff line, drawn in the card's colour once filled so it still reads. -->
            <path
              :d="answer.cuff"
              :stroke="
                vote === answer.value ? 'var(--surface-gray-1)' : 'currentColor'
              "
            />
          </svg>
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import { Button } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@app/routes";

// Values match HD Article Feedback: 1 like, 2 dislike; "0" clears, sent by a second click.
// Paths are lucide's thumbs-up and thumbs-down.
const ANSWERS = [
  {
    value: "1",
    label: __("Yes, it was helpful"),
    thumb:
      "M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z",
    cuff: "M7 10v12",
  },
  {
    value: "2",
    label: __("No, it wasn't helpful"),
    thumb:
      "M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z",
    cuff: "M17 14V2",
  },
];

defineProps<{
  vote?: string;
  onVote?: (value: string) => void;
  canRaiseTicket?: boolean;
}>();
</script>
