<template>
  <Button variant="outline" :label="label" @click="emit('click')">
    <template #prefix>
      <span
        class="shrink-0 rounded-full"
        :class="
          state === 'next'
            ? 'size-2.5 bg-surface-base shadow-[inset_0_0_0_2px_var(--ink-amber-7)]'
            : 'size-2 bg-[var(--ink-green-6)]'
        "
      />
    </template>
  </Button>
</template>

<script setup lang="ts">
// A choice marked with the summary rail's own dot rather than a button fill, so
// answering "did this solve it?" reads in the same language the timeline beside it
// already speaks: green filled for a milestone reached, an amber ring for one still
// open. The ring is an inset shadow, not a border, so it eats no geometry.
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
