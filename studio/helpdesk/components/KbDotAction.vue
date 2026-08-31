<template>
  <Button variant="outline" :label="label" @click="emit('click')">
    <template #prefix>
      <span class="kb-dot" :class="`kb-dot--${state}`" />
    </template>
  </Button>
</template>

<script setup lang="ts">
// A choice marked with the summary rail's own dot rather than a button fill, so
// answering "did this solve it?" reads in the same language the timeline beside it
// already speaks: green filled for a milestone reached, an amber ring for one still
// open.
//
// Outline, not ghost: on its own surface each answer reads as a thing to press, where a
// transparent one sat closer to the prompt's text than to a control. Neither is solid,
// because the dots carry the meaning and a filled button would imply a recommended answer.
import { Button } from "frappe-ui";

withDefaults(
  defineProps<{
    label?: string;
    /** Same names the rail uses: `done` is a filled dot, `next` an open ring. */
    state?: "done" | "next";
  }>(),
  { label: "", state: "done" }
);

const emit = defineEmits<{ click: [] }>();
</script>

<style scoped>
/* Geometry and colours lifted from KbTicketTimeline's rail. Plain CSS for the same
   reason it uses it: the ring is an inset box-shadow, not a border. */
.kb-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: var(--ink-green-6);
}

.kb-dot--next {
  width: 10px;
  height: 10px;
  background: var(--surface-base);
  box-shadow: inset 0 0 0 2px var(--ink-amber-7);
}
</style>
