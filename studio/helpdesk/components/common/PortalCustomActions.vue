<template>
  <CustomActions :actions="actions" />
</template>

<script setup lang="ts">
// Studio finds custom blocks only under the app folder, so the shared component reaches the block tree through this.
import CustomActions from "@helpdesk/shared/CustomActions.vue";

defineProps<{ actions?: any[] }>();
</script>
