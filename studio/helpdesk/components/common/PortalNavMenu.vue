<template>
  <Dropdown :options="options" :offset="4" align="start">
    <template #default="{ open }">
      <button
        type="button"
        class="flex h-9 min-w-0 max-w-64 cursor-pointer items-center gap-2 rounded-lg pe-2 ps-1.5 transition-colors hover:bg-surface-gray-3"
        :class="open ? 'bg-surface-gray-3' : 'bg-surface-gray-2'"
      >
        <img
          v-if="logo"
          :src="logo"
          alt=""
          aria-hidden="true"
          class="size-6 shrink-0 rounded-md object-contain"
        />
        <span class="truncate text-base font-medium text-ink-gray-8">
          {{ name }}
        </span>
        <Icon
          :icon="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          class="size-4 shrink-0 text-ink-gray-5"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { Dropdown, Icon } from "frappe-ui";

defineProps<{ options?: unknown[]; logo?: string; name?: string }>();
</script>
