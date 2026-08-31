<template>
  <div class="kb-timeline">
    <div
      v-for="(step, index) in steps"
      :key="step.title"
      class="kb-timeline__row"
    >
      <div class="kb-timeline__rail">
        <!-- The moment hangs off the marker it belongs to: the dot is the milestone, the
             line beside it is only how long it took to get there. -->
        <Tooltip
          :text="step.fullDate"
          :disabled="!step.fullDate"
          :hover-delay="0.2"
          placement="left"
        >
          <span
            class="kb-timeline__dot"
            :class="`kb-timeline__dot--${step.state}`"
          />
        </Tooltip>
        <span
          v-if="index < steps.length - 1"
          class="kb-timeline__line"
          :class="`kb-timeline__line--${steps[index + 1].state}`"
        />
      </div>
      <div class="kb-timeline__body">
        <div
          class="kb-timeline__title"
          :class="`kb-timeline__title--${step.state}`"
        >
          {{ step.title }}
        </div>
        <div v-if="step.subtitle" class="kb-timeline__meta">
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
</script>

<style scoped>
/* Plain CSS rather than utilities: the dashed rails are repeating gradients and the
   dots are inset box-shadow rings, neither of which reads well as a class soup. */
.kb-timeline {
  display: flex;
  flex-direction: column;
}

.kb-timeline__row {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr);
  gap: 12px;
}

.kb-timeline__rail {
  position: relative;
  display: flex;
  justify-content: center;
}

.kb-timeline__dot {
  position: relative;
  flex-shrink: 0;
  margin-top: 6px;
  width: 8px;
  height: 8px;
  border-radius: 9999px;
}

/* An 8px dot is a deliberate aim. This pads the target out to 24px without moving or
   resizing the mark itself — the pseudo-element hit-tests as part of the dot, so the
   tooltip catches a pointer passing nearby. */
.kb-timeline__dot::after {
  content: "";
  position: absolute;
  inset: -8px;
  border-radius: 9999px;
}

.kb-timeline__dot--done {
  background: var(--ink-green-6);
}

/* Closed is an ending, not an outcome — a ticket can close without ever being fixed,
   so it settles to grey rather than claiming the green of a resolution. */
.kb-timeline__dot--closed {
  background: var(--outline-gray-4);
}

.kb-timeline__dot--breach {
  background: var(--ink-red-6);
}

/* An open amber ring for what happens next — drawn a touch larger than the filled dots,
   with the margin pulling its centre back onto their axis. Only ever one per rail: a
   ring on every future row would mark nothing in particular. */
.kb-timeline__dot--next {
  margin-top: 5px;
  width: 10px;
  height: 10px;
  background: var(--surface-base);
  box-shadow: inset 0 0 0 2px var(--ink-amber-7);
}

/* Milestones queued behind the next one — present, but not asking for attention. */
.kb-timeline__dot--pending {
  background: var(--surface-base);
  box-shadow: inset 0 0 0 1.5px var(--outline-gray-4);
}

.kb-timeline__line {
  position: absolute;
  top: 18px;
  bottom: 0;
  width: 2px;
  border-radius: 9999px;
}

.kb-timeline__line--done,
.kb-timeline__line--closed {
  background: var(--outline-gray-2);
}

/* The dashes are a repeating gradient rather than a dashed border — the same trick
   the analytics rail uses, rotated from 90deg to 180deg. */
.kb-timeline__line--breach {
  background: repeating-linear-gradient(
    180deg,
    var(--ink-red-6) 0 5px,
    transparent 5px 11px
  );
}

.kb-timeline__line--next,
.kb-timeline__line--pending {
  background: repeating-linear-gradient(
    180deg,
    var(--outline-gray-2) 0 5px,
    transparent 5px 11px
  );
}

.kb-timeline__body {
  min-width: 0;
  padding-bottom: 20px;
}

.kb-timeline__row:last-child .kb-timeline__body {
  padding-bottom: 0;
}

.kb-timeline__title {
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--ink-gray-8);
}

/* Milestones queued behind the one being waited on: present, so the reader can see where
   this is going, but not competing with the step that is actually live. */
.kb-timeline__title--pending {
  color: var(--ink-gray-4);
}

.kb-timeline__meta {
  font-size: 12px;
  line-height: 18px;
  color: var(--ink-gray-5);
}
</style>
