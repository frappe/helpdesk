<template>
  <!-- A new key remounts the steps, which replays the fill. -->
  <div :key="run" class="flex flex-col">
    <div
      v-for="(step, index) in steps"
      :key="step.title"
      class="group grid grid-cols-[16px_minmax(0,1fr)] gap-3"
      :style="{ '--step': index }"
    >
      <div class="relative flex justify-center">
        <Tooltip
          :text="step.fullDate"
          :disabled="!step.fullDate"
          :hover-delay="200"
          side="left"
        >
          <span
            :class="[
              'timeline-dot',
              DOT_BASE,
              (step.late ? LATE_DOT_CLASSES : MILESTONE_DOT_CLASSES)[step.state],
              step.state === 'next' ? 'mt-[5px]' : 'mt-1.5',
            ]"
          />
        </Tooltip>
        <span
          v-if="index < steps.length - 1"
          :class="['timeline-line', LINE_BASE, LINE[steps[index + 1].state]]"
        />
      </div>
      <div class="timeline-text min-w-0 pb-5 group-last:pb-0">
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
import { inject, ref, watch, type Ref } from "vue";
import { Tooltip } from "frappe-ui";
import { LATE_DOT_CLASSES, MILESTONE_DOT_CLASSES, type MilestoneState } from "./milestoneDots";

interface TimelineStep {
  title: string;
  subtitle: string;
  // `next` is the nearest unmet milestone; `pending` is anything behind it.
  state: MilestoneState;
  fullDate?: string;
  // Overdue, or reached after its SLA deadline.
  late?: boolean;
}

// The ::after pads an 8px target out to 24px without moving or resizing the mark.
const DOT_BASE =
  "relative shrink-0 rounded-full after:absolute after:-inset-2 after:rounded-full after:content-['']";

const LINE_BASE = "absolute bottom-0 top-[18px] w-[0.05rem] rounded-full";

// A gradient, not a dashed border, so the dash length is ours.
const DASHED_OWED =
  "bg-[repeating-linear-gradient(180deg,var(--outline-gray-2)_0_5px,transparent_5px_11px)]";
const LINE: Record<MilestoneState, string> = {
  done: "bg-[var(--outline-gray-2)]",
  closed: "bg-[var(--outline-gray-2)]",
  next: DASHED_OWED,
  pending: DASHED_OWED,
};

withDefaults(defineProps<{ steps?: TimelineStep[] }>(), {
  steps: () => [],
});

const sectionOpen = inject<Ref<boolean>>("portalSectionOpen", ref(true));
const run = ref(0);
watch(sectionOpen, (open) => open && run.value++);
</script>

<style scoped>
/* On load each dot lands, then its line draws down to the next, so the fill runs to the latest status. */
@media (prefers-reduced-motion: no-preference) {
  .timeline-dot {
    animation: timeline-pop 220ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
    animation-delay: calc(var(--step) * 160ms);
  }
  .timeline-text {
    animation: timeline-fade 220ms ease-out both;
    animation-delay: calc(var(--step) * 160ms);
  }
  .timeline-line {
    transform-origin: top;
    animation: timeline-draw 120ms linear both;
    animation-delay: calc(var(--step) * 160ms + 40ms);
  }
}

@keyframes timeline-pop {
  from {
    opacity: 0;
    transform: scale(0.4);
  }
}

@keyframes timeline-fade {
  from {
    opacity: 0;
    transform: translateX(-4px);
  }
}

@keyframes timeline-draw {
  from {
    transform: scaleY(0);
  }
}
</style>
