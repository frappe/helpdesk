<template>
  <Dropdown :options="dropdownOptions">
    <template #default>
      <button
        class="flex items-center gap-1 hover:bg-transparent focus:outline-none"
      >
        <span class="text-ink-gray-7 text-p-sm">
          {{ currentStatus ? __(currentStatus) : __("Set status") }}
        </span>
        <LucideChevronDown class="size-4 text-ink-gray-5" />
      </button>
    </template>
    <template #item-prefix="{ item }">
      <div
        class="size-2 rounded-full flex-shrink-0"
        :class="agentStatusStore.statusColor(item.value)"
      />
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { useAvailability } from "@/composables/useAvailability";
import { useAgentStatusStore } from "@/stores/agentStatus";
import { __ } from "@/translation";
import { Dropdown } from "frappe-ui";
import { computed } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";

const { currentStatus, options, setStatus } = useAvailability();
const agentStatusStore = useAgentStatusStore();

const dropdownOptions = computed(() =>
  options.value.map((statusOption: string) => ({
    label: __(statusOption),
    value: statusOption,
    onClick: () => setStatus(statusOption),
  }))
);
</script>
