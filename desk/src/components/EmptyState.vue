<template>
  <div class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <!-- Icon -->
      <component v-if="icon" :is="icon" class="h-10 w-10" />
      <!-- title -->
      <span>{{ title }}</span>
      <!-- Button which emits Empty State Action -->
      <Button label="Create" @click="emit('emptyStateAction')" variant="subtle">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: "No Data Found",
  },
  icon: {
    type: String || HTMLElement,
    default: "",
  },
});

const emit = defineEmits(["emptyStateAction"]);
</script>

<style lang="scss" scoped></style>
