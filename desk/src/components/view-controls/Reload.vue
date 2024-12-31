<template>
  <Button label="Refresh" :loading="loading">
    <template #icon>
      <RefreshIcon class="h-4 w-4" />
    </template>
  </Button>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});
</script>
