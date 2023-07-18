<template>
  <div class="flex gap-2">
    <Button v-bind="secondary">
      <template #prefix>
        <Icon icon="lucide:x" class="h-4 w-4" />
      </template>
    </Button>
    <Button v-bind="primary">
      <template #prefix>
        <Icon icon="lucide:check" class="h-4 w-4" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Icon } from "@iconify/vue";

const emit = defineEmits<{
  (event: "create"): void;
  (event: "discard"): void;
}>();

const primary = {
  label: "Create",
  theme: "gray",
  variant: "solid",
  onClick: () => emit("create"),
};

const secondary = {
  label: "Discard",
  theme: "gray",
  variant: "subtle",
  onClick: () => emit("discard"),
};
</script>
