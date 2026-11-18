<template>
  <!-- v-model and classes fall through to Select. -->
  <Select>
    <template #item-prefix="{ item }">
      <span
        v-if="item.value === 'system'"
        class="flex size-3 shrink-0 overflow-hidden rounded-full border border-outline-gray-2"
      >
        <span class="w-1/2 bg-white" />
        <span class="w-1/2 bg-gray-950" />
      </span>
      <span
        v-else
        class="size-3 shrink-0 rounded-full border"
        :class="
          item.value === 'light'
            ? 'border-outline-gray-2 bg-white'
            : 'border-gray-950 bg-gray-950'
        "
      />
    </template>
  </Select>
</template>

<script setup lang="ts">
import { Select } from "frappe-ui";
</script>
