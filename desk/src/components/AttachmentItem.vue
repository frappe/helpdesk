<template>
  <Button :label="label" theme="gray" variant="outline">
    <template #prefix>
      <IconFile class="h-4 w-4 text-gray-700" />
    </template>
    <template #suffix>
      <slot name="suffix" />
    </template>
  </Button>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import IconFile from "~icons/lucide/file";

defineProps({
  label: {
    type: String,
    required: true,
  },
});
</script>
