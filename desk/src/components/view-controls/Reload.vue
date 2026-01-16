<template>
  <Button :label="__('Refresh')" :loading="loading">
    <template #icon>
      <RefreshIcon class="h-4 w-4" />
    </template>
  </Button>
</template>

<script setup>
import { __ } from "@/translation";

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
});
</script>
