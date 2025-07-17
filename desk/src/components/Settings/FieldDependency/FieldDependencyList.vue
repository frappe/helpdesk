<template>
  <div>
    <header class="flex justify-between mb-4">
      <div>
        <h1 class="text-lg font-semibold mb-1">Field Dependencies</h1>
        <p class="text-ink-gray-6 text-base">
          Dynamically control field options based on selection
        </p>
      </div>
      <Button
        label="New"
        variant="solid"
        size="sm"
        @click="$emit('update:step', 'fd')"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4 stroke-1.5" />
        </template>
      </Button>
    </header>

    <div class="w-full">
      <!-- table heading -->
      <div class="flex w-full p-2 border-b">
        <p class="w-4/12 text-p-sm text-ink-gray-5">Name</p>
        <p class="w-4/12 text-p-sm text-ink-gray-5">Created By</p>
        <p class="w-3/12 text-p-sm text-ink-gray-5">Enabled</p>
        <p class="w-1/12 text-p-sm text-ink-gray-5"></p>
      </div>

      <!-- Table content -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { createListResource } from "frappe-ui";

const list = createListResource({
  doctype: "HD Form Script",
  filters: { is_standard: 1 },
  fields: ["name", "enabled", "owner"],
  auto: true,
  cache: ["FD", "List"],
});
</script>

<style scoped></style>
