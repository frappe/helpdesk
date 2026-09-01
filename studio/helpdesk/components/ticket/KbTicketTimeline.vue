<template>
  <div class="flex flex-col">
    <div
      v-for="(step, index) in steps"
      :key="step.title"
      class="group grid grid-cols-[16px_minmax(0,1fr)] gap-3"
    >
      <div class="relative flex justify-center">
        <!-- The moment hangs off the marker it belongs to: the dot is the milestone, the
             line beside it is only how long it took to get there. -->
        <Tooltip
          :text="step.fullDate"
          :disabled="!step.fullDate"
          :hover-delay="0.2"
          placement="left"
        >
          <span :class="[DOT_BASE, DOT[step.state]]" />
        </Tooltip>
        <span
          v-if="index < steps.length - 1"
          :class="[LINE_BASE, LINE[steps[index + 1].state]]"
        />
      </div>
      <div class="min-w-0 pb-5 group-last:pb-0">
        <div
          class="text-base-medium"
          :class="step.state === 'pending' ? 'text-ink-gray-4' : 'text-ink-gray-8'"
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
// The ticket's lifecycle as a vertical rail — the agent portal's analytics status
// line (`desk/src/components/ticket-agent/analytics/TicketTimeline.vue`) turned on
// its side, because that one is a horizontally scrolled component and this sidebar
// is 382px wide. Its colours are kept exactly, so the two portals read as one system.
//
// A segment is the interval *leading to* the next milestone, so it takes that step's
// state: solid once reached, dashed while still owed.

import { Tooltip } from "frappe-ui";

export interface TimelineStep {
  title: string;
  subtitle: string;
  /** `next` is the nearest unmet milestone; `pending` is anything behind it. */
  state: "done" | "closed" | "next" | "pending" | "breach";
  /** The exact moment, shown on hover — the line itself reads as elapsed time. */
  fullDate?: string;
}

withDefaults(defineProps<{ steps?: TimelineStep[] }>(), {
  steps: () => [],
});

// An 8px dot is a deliberate aim: the ::after pads the target out to 24px without
// moving or resizing the mark, so the tooltip catches a pointer passing nearby.
const DOT_BASE =
  "relative shrink-0 rounded-full after:absolute after:-inset-2 after:rounded-full after:content-['']";

// Full literal class strings — Tailwind's scanner cannot see interpolation.
// The rings are inset shadows so they eat no geometry; `next` draws a touch larger,
// its margin pulling the centre back onto the filled dots' axis — only ever one per
// rail. Closed is an ending, not an outcome, so it settles to grey rather than
// claiming the green of a resolution.
const DOT: Record<TimelineStep["state"], string> = {
  done: "mt-1.5 size-2 bg-[var(--ink-green-6)]",
  closed: "mt-1.5 size-2 bg-[var(--outline-gray-4)]",
  breach: "mt-1.5 size-2 bg-[var(--ink-red-6)]",
  next: "mt-[5px] size-2.5 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-amber-7)]",
  pending:
    "mt-1.5 size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--outline-gray-4)]",
};

const LINE_BASE = "absolute bottom-0 top-[18px] w-0.5 rounded-full";

// The dashes are a repeating gradient rather than a dashed border — the same trick
// the analytics rail uses, rotated from 90deg to 180deg.
const DASHED_OWED =
  "bg-[repeating-linear-gradient(180deg,var(--outline-gray-2)_0_5px,transparent_5px_11px)]";
const LINE: Record<TimelineStep["state"], string> = {
  done: "bg-[var(--outline-gray-2)]",
  closed: "bg-[var(--outline-gray-2)]",
  breach:
    "bg-[repeating-linear-gradient(180deg,var(--ink-red-6)_0_5px,transparent_5px_11px)]",
  next: DASHED_OWED,
  pending: DASHED_OWED,
};
</script>
