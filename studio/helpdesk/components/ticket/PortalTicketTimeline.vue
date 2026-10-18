<template>
  <!-- A new key remounts the steps to replay the fill. -->
  <div :key="run" class="flex flex-col">
    <div
      v-for="(step, index) in steps"
      :key="step.title"
      class="group relative grid grid-cols-[16px_minmax(0,1fr)] gap-3"
      :style="{ '--step': index }"
    >
      <!-- Unpositioned so the hover area and line size to the row. -->
      <div class="flex justify-center">
        <Tooltip
          :text="step.fullDate"
          :disabled="!step.fullDate"
          :hover-delay="200"
          side="left"
        >
          <span :class="[HOVER_AREA, 'mt-1.5']">
            <span
              :class="[
                'timeline-dot',
                DOT_BASE,
                (step.late ? LATE_DOT_CLASSES : MILESTONE_DOT_CLASSES)[
                  step.state
                ],
              ]"
            />
          </span>
        </Tooltip>
        <span
          v-if="index < steps.length - 1"
          :class="['timeline-line', LINE_BASE, LINE[steps[index + 1].state]]"
        />
      </div>
      <!-- Fixed 56px steps so the dots sit evenly. -->
      <div class="timeline-text min-h-14 min-w-0 group-last:min-h-0">
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
  next: "size-2 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-amber-7)]",
  pending:
    "size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--outline-gray-4)]",
};

const LATE_DOT_CLASSES = {
  done: "size-2 bg-[var(--ink-red-6)]",
  closed: "size-2 bg-[var(--ink-red-6)]",
  next: "size-2 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-red-6)]",
  pending: "size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--ink-red-6)]",
};

type MilestoneState = keyof typeof MILESTONE_DOT_CLASSES;

interface TimelineStep {
  title: string;
  subtitle: string;
  // `next`: nearest unmet milestone; `pending`: the rest.
  state: MilestoneState;
  fullDate?: string;
  late?: boolean;
}

const DOT_BASE = "shrink-0 rounded-full";

// ::after makes the whole row the hover target; off the dot, whose transform would shrink it.
const HOVER_AREA =
  "flex shrink-0 self-start after:absolute after:inset-0 after:z-[1] after:content-['']";

const LINE_BASE = "absolute bottom-0 top-[18px] w-[0.05rem] rounded-full";

// Gradient, not a dashed border, to control dash length.
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
