<template>
  <Button
    :key="label"
    theme="gray"
    variant="outline"
    :label="label"
    :disabled="disabled"
  >
    <template #suffix>
      <IconX class="h-3 w-3" @click="handleClick(label)" />
    </template>
  </Button>
</template>
<script setup>
import { Button } from "frappe-ui";
import IconX from "~icons/lucide/x";
defineProps({
  label: {
    type: String,
    default: "Button",
    require: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["click"]);

const handleClick = (label) => {
  emit("click", label);
};
</script>
