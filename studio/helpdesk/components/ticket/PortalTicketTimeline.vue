<template>
  <!-- No steps yet: a closed ticket waits on its close history. -->
  <PortalSkeleton v-if="!steps.length" variant="timeline-steps" :count="5" />
  <!-- A new key remounts the steps to replay the fill. -->
  <div v-else :key="run" class="flex flex-col">
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
          <span :class="[HOVER_AREA, 'mt-1']">
            <span
              aria-hidden="true"
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
        <div class="text-base-medium" :class="TITLE_CLASSES[step.state]">
          {{ step.title }}
        </div>
        <div
          v-if="step.subtitle"
          class="text-p-xs"
          :class="
            step.state === 'skipped' ? 'text-ink-gray-4' : 'text-ink-gray-5'
          "
        >
          {{ step.subtitle }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, watch, type Ref } from "vue";
import { Tooltip } from "frappe-ui";
import PortalSkeleton from "@app/components/ui/PortalSkeleton.vue";

// Full literal strings: Tailwind's scanner cannot see interpolation.
const MILESTONE_DOT_CLASSES = {
  done: "size-2 bg-[var(--ink-green-6)]",
  closed: "size-2 bg-[var(--outline-gray-4)]",
  next: "size-2 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-amber-7)]",
  pending:
    "size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--outline-gray-4)]",
  // The pending ring with a dash through it.
  skipped:
    "size-2 flex items-center justify-center bg-surface-base shadow-[inset_0_0_0_1.5px_var(--outline-gray-4)] after:h-[1.5px] after:w-1 after:bg-[var(--outline-gray-4)] after:content-['']",
};

const LATE_DOT_CLASSES = {
  done: "size-2 bg-[var(--ink-red-6)]",
  closed: "size-2 bg-[var(--ink-red-6)]",
  next: "size-2 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-red-6)]",
  pending: "size-2 bg-surface-base shadow-[inset_0_0_0_1.5px_var(--ink-red-6)]",
  skipped: MILESTONE_DOT_CLASSES.skipped,
};

const TITLE_CLASSES: Record<MilestoneState, string> = {
  done: "text-ink-gray-8",
  closed: "text-ink-gray-8",
  next: "text-ink-gray-8",
  pending: "text-ink-gray-4",
  skipped: "text-ink-gray-4 line-through decoration-[var(--outline-gray-4)]",
};

type MilestoneState = keyof typeof MILESTONE_DOT_CLASSES;

interface TimelineStep {
  title: string;
  subtitle: string;
  // `next`: nearest unmet milestone; `pending`: the rest; `skipped`: closed before it.
  state: MilestoneState;
  fullDate?: string;
  late?: boolean;
}

const DOT_BASE = "shrink-0 rounded-full";

// ::after makes the whole row the hover target; off the dot, whose transform would shrink it.
const HOVER_AREA =
  "flex shrink-0 self-start after:absolute after:inset-0 after:z-[1] after:content-['']";

// Starts 4px below the dot (mt-1 + size-2), the gap the line above leaves.
const LINE_BASE = "absolute bottom-0 top-4 w-[0.05rem] rounded-full";

// Gradient, not a dashed border, to control dash length.
const DASHED_OWED =
  "bg-[repeating-linear-gradient(180deg,var(--outline-gray-2)_0_5px,transparent_5px_11px)]";
const LINE: Record<MilestoneState, string> = {
  done: "bg-[var(--outline-gray-2)]",
  closed: "bg-[var(--outline-gray-2)]",
  next: DASHED_OWED,
  pending: DASHED_OWED,
  skipped: DASHED_OWED,
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
  }
}

@keyframes timeline-draw {
  from {
    transform: scaleY(0);
  }
}
</style>
