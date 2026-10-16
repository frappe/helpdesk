<template>
  <svg
    viewBox="0 0 24 24"
    :fill="filled ? 'currentColor' : 'none'"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="PATHS[answer].thumb" />
    <!-- The cuff line, drawn in the background's colour once filled so it still reads. -->
    <path
      :d="PATHS[answer].cuff"
      :stroke="filled ? background : 'currentColor'"
    />
  </svg>
</template>

<script setup lang="ts">
// Inline, not a lucide class: the chosen answer's thumb fills, which a mask icon cannot.
// Lucide's thumbs-up and thumbs-down; keys match HD Article Feedback: 1 like, 2 dislike.
const PATHS = {
  "1": {
    thumb:
      "M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z",
    cuff: "M7 10v12",
  },
  "2": {
    thumb:
      "M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z",
    cuff: "M17 14V2",
  },
};

defineProps<{ answer: 1 | 2; filled?: boolean; background: string }>();
</script>
