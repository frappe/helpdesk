<template>
  <div class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <!-- Icon -->
      <component v-if="icon" :is="icon" class="h-10 w-10" />
      <!-- title -->
      <span>{{ title || __("No Data Found") }}</span>
      <!-- Button which emits Empty State Action -->
      <Button
        :label="__('Create')"
        @click="emit('emptyStateAction')"
        variant="subtle"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { VNode } from "vue";
import { __ } from "@/translation";

interface Props {
  title: string;
  icon?: VNode | string;
}

withDefaults(defineProps<Props>(), {
  title: "",
  icon: "",
});

const emit = defineEmits(["emptyStateAction"]);
</script>

<style lang="scss" scoped></style>
