<template>
  <div class="flex flex-col">
    <span class="text-xs text-gray-500">{{ label }}</span>
    <span class="text-xl font-semibold" :style="{ color }">{{ value }}</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string;
  value: string | number;
  color?: string;
}

withDefaults(defineProps<Props>(), {
  color: "#318AD8",
});
</script>
