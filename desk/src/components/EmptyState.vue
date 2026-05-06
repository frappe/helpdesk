<template>
  <div class="flex h-full items-center justify-center w-[stretch]">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4 w-9/12 md:w-4/12"
    >
      <!-- overlay variant (for charts) -->
      <div
        v-if="variant === 'overlay'"
        class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none -z-10"
        :style="{
          backgroundImage:
            'radial-gradient(ellipse at center, rgba(255, 255, 255, 1) 30%, rgba(255, 255, 255, 0.8) 30%, rgba(255, 255, 255, 0) 70%)',
        }"
      />
      <!-- Icon -->
      <component v-if="icon" :is="icon" class="h-10 w-10" />
      <!-- title -->
      <div class="flex flex-col items-center justify-center">
        <span
          :class="{
            'text-sm font-medium text-ink-gray-8': text === 'sm',
            'text-base font-medium text-ink-gray-8': text === 'md' || !text,
            'text-lg font-medium text-ink-gray-8': text === 'lg',
          }"
        >
          {{ __(title) }}
        </span>
        <span
          v-if="descriptionText"
          :class="{
            'text-center text-xs text-ink-gray-6 mt-1': text === 'sm',
            'text-center text-sm text-ink-gray-6 mt-1': text === 'md' || !text,
            'text-center text-base text-ink-gray-6 mt-1': text === 'lg',
          }"
        >
          {{ __(descriptionText) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { VNode, computed } from "vue";
interface Props {
  title: string;
  icon?: VNode | string;
  description?: string;
  variant?: "default" | "overlay";
  text?: "sm" | "md" | "lg";
}

const props = withDefaults(defineProps<Props>(), {
  title: "No Data Found",
  icon: "",
  variant: "default",
  text: "lg",
});

const descriptionText = computed(() =>
  props.description !== undefined && props.description !== ""
    ? props.description
    : `Create new ${props.title
        .split(" ")[1]
        .toLocaleLowerCase()} using the Create button.`
);
</script>

<style lang="scss" scoped></style>
