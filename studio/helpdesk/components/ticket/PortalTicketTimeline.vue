<template>
  <!-- A new key remounts the steps, which replays the fill. -->
  <div :key="run" class="flex flex-col">
    <div
      v-for="(step, index) in steps"
      :key="step.title"
      class="group relative grid grid-cols-[16px_minmax(0,1fr)] gap-3"
      :style="{ '--step': index }"
    >
      <!-- Not positioned, so the hover area and the line measure against the row. -->
      <div class="flex justify-center">
        <Tooltip
          :text="step.fullDate"
          :disabled="!step.fullDate"
          :hover-delay="200"
          side="left"
        >
          <span
            :class="[
              HOVER_AREA,
              step.state === 'next' ? 'mt-[5px]' : 'mt-1.5',
            ]"
          >
            <span
              :class="[
                'timeline-dot',
                DOT_BASE,
                (step.late ? LATE_DOT_CLASSES : MILESTONE_DOT_CLASSES)[step.state],
              ]"
            />
          </span>
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

// Full literal strings: Tailwind's scanner cannot see interpolation.
const MILESTONE_DOT_CLASSES = {
  done: "size-2 bg-[var(--ink-green-6)]",
  closed: "size-2 bg-[var(--outline-gray-4)]",
  next: "size-2.5 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-amber-7)]",
  pending:
    "size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--outline-gray-4)]",
};

// Overdue or missed: the same shape, in red.
const LATE_DOT_CLASSES = {
  done: "size-2 bg-[var(--ink-red-6)]",
  closed: "size-2 bg-[var(--ink-red-6)]",
  next: "size-2.5 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-red-6)]",
  pending: "size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--ink-red-6)]",
};

type MilestoneState = keyof typeof MILESTONE_DOT_CLASSES;

interface TimelineStep {
  title: string;
  subtitle: string;
  // `next` is the nearest unmet milestone; `pending` is anything behind it.
  state: MilestoneState;
  fullDate?: string;
  // Overdue, or reached after its SLA deadline.
  late?: boolean;
}

const DOT_BASE = "shrink-0 rounded-full";

// Wraps the dot, so the tooltip points at it, while the ::after stretches over the row so hovering any
// part of the step opens it. Kept off the animated dot: a transform would shrink the ::after back to the
// dot, and z-[1] keeps it above the text while the text's fade-in transform stacks the text on top.
const HOVER_AREA =
  "flex shrink-0 self-start after:absolute after:inset-0 after:z-[1] after:content-['']";

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
