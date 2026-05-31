<template>
  <span class="text-base text-ink-gray-9">
    {{ priority }}
  </span>
</template>

<script setup>
defineProps({
  priority: {
    type: String,
    required: true,
  },
});
</script>