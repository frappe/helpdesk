<template>
  <Dropdown :options="options" :offset="4" align="start">
    <template #default="{ open }">
      <button
        type="button"
        :aria-label="name"
        class="-ms-2 flex h-8 min-w-0 max-w-[15rem] cursor-pointer items-center gap-2 rounded-5 px-2 transition-colors duration-300 ease-in-out"
        :class="open ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-3'"
      >
        <img
          v-if="logo"
          :src="logo"
          alt=""
          aria-hidden="true"
          class="size-6 shrink-0 rounded-2 object-contain"
        />
        <span
          class="hidden truncate text-base-medium text-ink-gray-9 sm:block"
        >
          {{ name }}
        </span>
        <Icon
          icon="lucide-chevron-down"
          class="size-4 shrink-0 text-ink-gray-5 transition-transform duration-200"
          :class="{ 'rotate-180': open }"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { Dropdown, Icon } from "frappe-ui";

defineProps<{ options?: unknown[]; logo?: string; name?: string }>();
</script>
