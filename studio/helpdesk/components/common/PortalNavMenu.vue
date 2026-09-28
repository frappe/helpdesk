<template>
  <Dropdown :options="options" :offset="4" align="start">
    <template #default="{ open }">
      <button
        type="button"
        class="group flex cursor-pointer items-center gap-1 rounded-5 bg-transparent p-0.5"
        :aria-label="__('Menu')"
      >
        <img
          v-if="logo"
          :src="logo"
          alt=""
          aria-hidden="true"
          class="size-8 shrink-0 object-contain"
        />
        <span v-else class="size-8 shrink-0" />
        <Icon
          :icon="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          class="size-4 shrink-0 transition-colors duration-150 group-hover:text-ink-gray-9"
          :class="open ? 'text-ink-gray-9' : 'text-ink-gray-5'"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
// Menu and trigger together: a trigger has to read its menu's state, and only the slot
// knows it. The chevron alone answers the pointer, with no fill behind the brand mark.
import { Dropdown, Icon } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";

defineProps<{ options?: unknown[]; logo?: string }>();
</script>
