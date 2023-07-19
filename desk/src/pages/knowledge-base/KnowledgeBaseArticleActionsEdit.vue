<template>
  <div class="flex gap-2">
    <Button v-bind="secondary">
      <template #prefix>
        <IconReset class="h-4 w-4" />
      </template>
    </Button>
    <Button v-bind="primary">
      <template #prefix>
        <IconSave class="h-4 w-4" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import IconSave from "~icons/lucide/save";
import IconReset from "~icons/lucide/rotate-ccw";

const emit = defineEmits<{
  (event: "save"): void;
  (event: "cancel"): void;
}>();

const primary = {
  label: "Save",
  theme: "gray",
  variant: "solid",
  onClick: () => emit("save"),
};

const secondary = {
  label: "Cancel",
  theme: "gray",
  variant: "subtle",
  onClick: () => emit("cancel"),
};
</script>
