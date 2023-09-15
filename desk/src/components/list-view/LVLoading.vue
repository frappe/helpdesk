<template>
  <div class="animate-pulse divide-y overflow-y-auto px-2.5">
    <div
      v-for="i in 20"
      :key="i"
      class="flex h-10 w-full items-center space-x-2 px-5"
    >
      <div v-if="checkbox" class="h-3.5 w-3.5 rounded-sm bg-gray-200" />
      <div
        v-for="c in columns"
        :key="c.key"
        class="flex items-center space-x-2"
      >
        <div v-if="!hiddenColumns.has(c.key)" :class="[c.width]">
          <div class="h-4 rounded-sm bg-gray-200" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { useColumns } from "@/composables/columns";
import { CheckboxKey, ColumnsKey, IdKey } from "./symbols";

const checkbox = inject(CheckboxKey);
const columns = inject(ColumnsKey);
const id = inject(IdKey);
const { storage: hiddenColumns } = useColumns(id);
</script>
