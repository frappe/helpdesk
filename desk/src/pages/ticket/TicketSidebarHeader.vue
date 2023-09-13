<template>
  <div class="flex items-center justify-between border-b px-5 py-3">
    <span class="text-lg font-semibold text-gray-900">
      {{ title }}
    </span>
    <Button theme="gray" variant="ghost" @click="() => $parent.$emit('close')">
      <template #icon>
        <LucideX class="h-4 w-4" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
interface P {
  title: string;
}

defineProps<P>();
</script>
