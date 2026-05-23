<template>
  <div class="flex items-center gap-3">
    <div
      class="flex h-10 w-10 items-center justify-center rounded-md ring-1 ring-outline-gray-modals"
    >
      <img v-if="icon" :src="icon" :alt="name" class="h-7 w-7 object-contain" />
      <LucideMail v-else class="h-5 w-5 text-ink-gray-7" />
    </div>
    <div class="flex flex-col">
      <div class="flex items-center gap-2">
        <span class="text-p-base font-medium text-ink-gray-8">
          {{ heading }}
        </span>
        <slot name="suffix" />
      </div>
      <div class="text-p-sm text-ink-gray-6">
        {{ subheading }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LucideMail from "~icons/lucide/mail";

interface Props {
  name: string;
  icon?: string;
  heading: string;
  subheading: string;
}

withDefaults(defineProps<Props>(), { icon: "" });
</script>
