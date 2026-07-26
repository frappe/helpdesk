<template>
  <div
    v-if="variant === 'badge'"
    class="flex flex-col items-center justify-center gap-4 absolute inset-x-0 top-5.5 bottom-0 pointer-events-none"
  >
    <div
      class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
    >
      <component v-if="icon" :is="icon" class="size-6 text-ink-gray-6" />
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="text-base-medium text-ink-gray-6">
        {{ __(title) }}
      </div>
      <div
        v-if="descriptionText"
        class="text-p-sm text-ink-gray-5 max-w-60 text-center"
      >
        {{ __(descriptionText) }}
      </div>
    </div>
  </div>
  <div
    v-else
    class="flex h-full items-center justify-center absolute inset-x-0 top-0 pointer-events-none"
  >
    <div
      class="flex flex-col items-center gap-2 text-2xl-medium text-ink-gray-4 w-9/12 md:w-4/12"
    >
      <!-- overlay variant (for charts) -->
      <div
        v-if="variant === 'overlay'"
        class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none -z-10"
        :style="{
          backgroundImage:
            'radial-gradient(ellipse at center, var(--surface-base) 10%, color-mix(in srgb, var(--surface-base) 90%, transparent) 25%, transparent 70%)',
        }"
      />
      <!-- Icon -->
      <component v-if="icon" :is="icon" class="h-10 w-10" />
      <!-- title -->
      <div class="flex flex-col items-center justify-center gap-0.5">
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
            'text-center text-p-xs text-ink-gray-6 mt-1': text === 'sm',
            'text-center text-p-sm text-ink-gray-6 mt-1':
              text === 'md' || !text,
            'text-center text-p-base text-ink-gray-6 mt-1': text === 'lg',
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
  variant?: "default" | "overlay" | "badge";
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
