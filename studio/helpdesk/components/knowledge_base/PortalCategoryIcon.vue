<!-- Studio only finds custom blocks under the app folder. -->
<template>
  <CategoryIcon :icon="icon" />
</template>

<script setup lang="ts">
import CategoryIcon from "@helpdesk/shared/CategoryIcon.vue"

defineProps<{ icon?: string | null }>()
</script>
