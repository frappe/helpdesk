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
// Marked with the summary rail's own dots, so the answers speak its language. Neither is
// solid: the dots carry the meaning, and a filled button would imply a recommended answer.
import { Button } from "frappe-ui";

withDefaults(
  defineProps<{
    label?: string;
    // Same names the rail uses: `done` is a filled dot, `next` an open ring.
    state?: "done" | "next";
  }>(),
  { label: "", state: "done" }
);

const emit = defineEmits<{ click: [] }>();
</script>
