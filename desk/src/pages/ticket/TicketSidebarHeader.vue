<template>
  <div class="flex items-center justify-between border-b px-5 py-3">
    <span class="text-lg font-semibold text-gray-900">
      {{ title }}
    </span>
    <Button theme="gray" variant="ghost" @click="() => $parent.$emit('close')">
      <template #icon>
        <Icon icon="lucide:x" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Icon } from "@iconify/vue";

interface P {
  title: string;
}

defineProps<P>();
</script>
