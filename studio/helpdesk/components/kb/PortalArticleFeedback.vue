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
          <PortalVoteThumb
            :answer="answer.value"
            :filled="vote === answer.value"
            background="var(--surface-gray-1)"
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
import PortalVoteThumb from "@app/components/kb/PortalVoteThumb.vue";
import { ROUTES } from "@app/routes";

// Values match HD Article Feedback: 1 like, 2 dislike; "0" clears, sent by a second click.
const ANSWERS = [
  { value: "1", label: __("Yes, it was helpful") },
  { value: "2", label: __("No, it wasn't helpful") },
];

defineProps<{
  vote?: string;
  onVote?: (value: string) => void;
  canRaiseTicket?: boolean;
}>();
</script>
