<template>
  <div v-if="step === 'fd-list'" class="h-full">
    <FieldDependencyList @update:step="updateStep" />
  </div>
  <div v-else-if="step === 'fd'" class="h-full">
    <FieldDependency
      @update:step="updateStep"
      :field-dependency-name="fieldDependencyName"
    />
  </div>
</template>

<script setup lang="ts">
import { Ref, ref } from "vue";
import FieldDependency from "./FieldDependency.vue";
import FieldDependencyList from "./FieldDependencyList.vue";

type FieldDependencyStep = "fd-list" | "fd";

const step: Ref<FieldDependencyStep> = ref("fd-list");
const fieldDependencyName = ref("");

function updateStep(
  newStep: FieldDependencyStep,
  fieldDependency?: string
): void {
  step.value = newStep;
  fieldDependencyName.value = fieldDependency;
}
</script>

<style scoped></style>
