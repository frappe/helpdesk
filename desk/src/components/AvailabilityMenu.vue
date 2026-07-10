<template>
  <Select
    :model-value="agentStatusStore.myStatus"
    :options="dropdownOptions"
    :placeholder="__('Set status')"
    variant="subtle"
    @update:model-value="agentStatusStore.setMyStatus"
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
import { useAgentStatusStore } from "@/stores/agentStatus";
import { __ } from "@/translation";
import { Select } from "frappe-ui";
import { computed } from "vue";

const agentStatusStore = useAgentStatusStore();

const dropdownOptions = computed(() =>
  agentStatusStore.statusOptions.map((statusOption: string) => ({
    label: __(statusOption),
    value: statusOption,
  }))
);
</script>
