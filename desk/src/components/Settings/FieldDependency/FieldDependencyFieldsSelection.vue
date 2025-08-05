<template>
  <div class="flex gap-3 w-full justify-between flex-1">
    <div class="flex-1 flex flex-col gap-1.5">
      <span class="block text-xs text-ink-gray-5"
        >Parent Field <span class="text-ink-red-3 select-none">*</span>
      </span>
      <Combobox
        v-model="state.selectedParentField"
        :options="parentFields"
        :disabled="!isNew"
      />
    </div>
    <div class="flex-1 flex flex-col gap-1.5">
      <span class="block text-xs text-ink-gray-5"
        >Child Field <span class="text-ink-red-3 select-none">*</span>
      </span>
      <Combobox
        v-model="state.selectedChildField"
        :options="state.childFields"
        :disabled="!state.selectedParentField || !isNew"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { FieldCriteriaState } from "@/types";
import { Combobox } from "frappe-ui";

const state = defineModel<FieldCriteriaState>();

const props = defineProps<{
  isNew: boolean;
  parentFields: any[];
}>();
</script>

<style scoped></style>
