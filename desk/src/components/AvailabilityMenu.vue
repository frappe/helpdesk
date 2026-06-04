<template>
  <Select
    :model-value="currentStatus"
    :options="dropdownOptions"
    :placeholder="__('Set status')"
    variant="subtle"
    @update:model-value="setStatus"
  >
    <template #item-prefix="{ option }">
      <div
        class="size-2 rounded-full flex-shrink-0"
        :class="agentStatusStore.statusColor(option.value)"
      />
    </template>
  </Select>
</template>

<script setup lang="ts">
import { useAvailability } from "@/composables/useAvailability";
import { useAgentStatusStore } from "@/stores/agentStatus";
import { __ } from "@/translation";
import { Select } from "frappe-ui";
import { computed } from "vue";

const { currentStatus, options, setStatus } = useAvailability();
const agentStatusStore = useAgentStatusStore();

const dropdownOptions = computed(() =>
  options.value.map((statusOption: string) => ({
    label: __(statusOption),
    value: statusOption,
  }))
);
</script>
