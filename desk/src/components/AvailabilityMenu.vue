<template>
  <Select
    class="w-full pl-0 hover:!bg-transparent focus:!bg-transparent"
    variant="ghost"
    :model-value="currentStatus || undefined"
    :options="optionsForSelect"
    :placeholder="__('Set status')"
    @update:model-value="(val) => val && setStatus(String(val))"
  >
    <template #trigger="{ displayValue }">
      <span class="text-ink-gray-7 text-p-sm">
        {{ displayValue || __("Set status") }}
      </span>
      <LucideChevronDown class="size-3 text-ink-gray-4" />
    </template>
    <template #item-prefix="{ option }">
      <div
        class="size-2 rounded-full flex-shrink-0"
        :class="statusColor(option.value)"
      />
    </template>
  </Select>
</template>

<script setup lang="ts">
import { statusColor, useAvailability } from "@/composables/useAvailability";
import { __ } from "@/translation";
import { Select } from "frappe-ui";
import { computed } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";

const { currentStatus, options, setStatus } = useAvailability();

const optionsForSelect = computed(() =>
  options.value.map((opt) => ({ label: __(opt), value: opt }))
);
</script>
