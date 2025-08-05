<template>
  <div class="flex gap-3 w-full justify-between">
    <FormControl
      v-model="state.selectedParentField"
      label="Parent Field"
      placeholder="Select Parent Field"
      required
      class="flex-1"
      type="select"
      :options="parentFields"
      :disabled="!isNew"
    />
    <FormControl
      v-model="state.selectedChildField"
      label="Child Field"
      placeholder="Select Child Field"
      required
      class="flex-1"
      :disabled="!state.selectedParentField || !isNew"
      type="select"
      :options="state.childFields"
    />
  </div>
</template>

<script setup lang="ts">
import { FieldCriteriaState } from "@/types";

const state = defineModel<FieldCriteriaState>();

const props = defineProps<{
  isNew: boolean;
  parentFields: any[];
}>();
</script>

<style scoped></style>
