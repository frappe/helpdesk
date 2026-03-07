<template>
  <div class="flex h-full items-center justify-center w-[stretch]">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4 w-4/12"
    >
      <!-- Icon -->
      <component v-if="icon" :is="icon" class="h-10 w-10" />
      <!-- title -->
      <div class="flex flex-col items-center justify-center">
        <span class="text-lg font-medium text-ink-gray-8">{{ __(title) }}</span>
        <span class="text-center text-p-base text-ink-gray-6 mt-1">
          {{ __(descriptionText) }}
        </span>
      </div>

      <!-- Button which emits Empty State Action -->
      <!-- <Button label="Create" @click="emit('emptyStateAction')" variant="subtle">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { VNode, computed } from "vue";
interface Props {
  title: string;
  icon?: VNode | string;
  description: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: "No Data Found",
  icon: "",
  description: "Create new data using the Create Button.",
});

const descriptionText = computed(
  () =>
    `Create new  ${props.title.split(" ")[1].toLocaleLowerCase()}
      using the Create button.` || props.description
);

const emit = defineEmits(["emptyStateAction"]);
</script>

<style lang="scss" scoped></style>
