<template>
  <div v-if="files.length" class="flex flex-wrap gap-2">
    <div
      v-for="(file, index) in files"
      :key="index"
      class="flex h-7 min-w-0 max-w-64 items-center gap-1 rounded-4 bg-surface-red-1 pl-2 text-p-sm text-ink-red-4"
    >
      <LucideCircleAlert class="size-3.5 shrink-0" aria-hidden="true" />
      <span class="truncate" :title="__('Could not upload {0}', [file.name])">
        {{ file.name }}
      </span>
      <Button
        variant="ghost"
        size="sm"
        :icon="LucideRotateCw"
        :tooltip="__('Retry upload')"
        :aria-label="__('Retry uploading {0}', [file.name])"
        @click="emit('retry', file)"
      />
      <Button
        variant="ghost"
        size="sm"
        :icon="LucideX"
        :aria-label="__('Remove {0}', [file.name])"
        @click="emit('remove', file)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import LucideCircleAlert from "~icons/lucide/circle-alert";
import LucideRotateCw from "~icons/lucide/rotate-cw";
import LucideX from "~icons/lucide/x";
import { __ } from "./translation";

defineProps<{ files: File[] }>();

const emit = defineEmits<{ retry: [file: File]; remove: [file: File] }>();
</script>
