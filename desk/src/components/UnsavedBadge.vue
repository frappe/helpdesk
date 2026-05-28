<template>
  <Transition name="fade">
    <Badge
      v-if="show"
      variant="subtle"
      theme="orange"
      size="sm"
      :label="__('Unsaved')"
    />
  </Transition>
</template>

<script setup lang="ts">
import { __ } from "@/translation";

defineProps<{ show: boolean }>();
</script>
