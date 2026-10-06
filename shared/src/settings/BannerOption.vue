<template>
  <button
    type="button"
    class="flex w-full flex-col gap-1.5 text-left"
    @click="emit('click')"
  >
    <span
      class="flex h-16 w-full items-center justify-center rounded-5 outline outline-2 outline-offset-2 transition-[outline-color]"
      :class="[
        background
          ? 'shadow-[inset_0_0_0_1px_rgba(0,0,0,0.06)]'
          : 'border border-outline-gray-2 bg-surface-gray-1 hover:bg-surface-gray-2',
        selected ? 'outline-[--ink-gray-9]' : 'outline-transparent',
        $attrs.class,
      ]"
      :style="background ? { background } : undefined"
    >
      <slot />
    </span>
    <span class="truncate text-sm text-ink-gray-6">{{ label }}</span>
  </button>
</template>

<script setup lang="ts">
defineOptions({ inheritAttrs: false });
defineProps<{ label: string; selected: boolean; background?: string }>();
const emit = defineEmits<{ click: [] }>();
</script>
