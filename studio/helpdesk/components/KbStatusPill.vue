<template>
  <span class="kb-pill">
    <span class="kb-pill__dot" :style="{ background: color }" />
    <span class="kb-pill__label">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
// Where the ticket stands, in the colour HD Ticket Status gives it — the same dot the
// portal's ticket list draws, so one ticket reads the same in both places. The colour
// arrives resolved (`statusMeta` in `ticketCells.ts` maps it to an espresso token),
// because a class built here from a status name would be purged: nothing else in the
// bundle uses it and this app sits outside the bench's Tailwind content globs.

withDefaults(defineProps<{ label?: string; color?: string }>(), {
  label: "",
  color: "var(--ink-gray-6)",
});
</script>

<style scoped>
.kb-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

/* The rail's dot geometry, so the header and the timeline read as one system. */
.kb-pill__dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 9999px;
}

/* `text-p-sm`, as the Team and Priority rows beneath it are set. */
.kb-pill__label {
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-gray-8);
  white-space: nowrap;
}
</style>
