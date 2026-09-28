<template>
  <div class="flex flex-col">
    <div
      v-for="(step, index) in steps"
      :key="step.title"
      class="group grid grid-cols-[16px_minmax(0,1fr)] gap-3"
    >
      <div class="relative flex justify-center">
        <!-- The dot is the milestone; the line beside it is only how long it took. -->
        <Tooltip
          :text="step.fullDate"
          :disabled="!step.fullDate"
          :hover-delay="200"
          side="left"
        >
          <span
            :class="[
              DOT_BASE,
              MILESTONE_DOT_CLASSES[step.state],
              step.state === 'next' ? 'mt-[5px]' : 'mt-1.5',
            ]"
          />
        </Tooltip>
        <span
          v-if="index < steps.length - 1"
          :class="[LINE_BASE, LINE[steps[index + 1].state]]"
        />
      </div>
      <div class="min-w-0 pb-5 group-last:pb-0">
        <div
          class="text-base-medium"
          :class="
            step.state === 'pending' ? 'text-ink-gray-4' : 'text-ink-gray-8'
          "
        >
          {{ step.title }}
        </div>
        <div v-if="step.subtitle" class="text-p-xs text-ink-gray-5">
          {{ step.subtitle }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// The analytics status line turned on its side, since this sidebar is only 382px wide.
// A segment leads to the next milestone, so it takes that step's state.
import { Tooltip } from "frappe-ui";
import { MILESTONE_DOT_CLASSES, type MilestoneState } from "./milestoneDots";

export interface TimelineStep {
  title: string;
  subtitle: string;
  // `next` is the nearest unmet milestone; `pending` is anything behind it.
  state: MilestoneState;
  // The exact moment, shown on hover; the line itself reads as elapsed time.
  fullDate?: string;
}

withDefaults(defineProps<{ steps?: TimelineStep[] }>(), {
  steps: () => [],
});

// The ::after pads an 8px target out to 24px without moving or resizing the mark.
const DOT_BASE =
  "relative shrink-0 rounded-full after:absolute after:-inset-2 after:rounded-full after:content-['']";

const LINE_BASE = "absolute bottom-0 top-[18px] w-[0.05rem] rounded-full";

// A repeating gradient, not a dashed border: the analytics rail's trick, rotated.
const DASHED_OWED =
  "bg-[repeating-linear-gradient(180deg,var(--outline-gray-2)_0_5px,transparent_5px_11px)]";
const LINE: Record<MilestoneState, string> = {
  done: "bg-[var(--outline-gray-2)]",
  closed: "bg-[var(--outline-gray-2)]",
  breach:
    "bg-[repeating-linear-gradient(180deg,var(--ink-red-6)_0_5px,transparent_5px_11px)]",
  next: DASHED_OWED,
  pending: DASHED_OWED,
};
</script>
