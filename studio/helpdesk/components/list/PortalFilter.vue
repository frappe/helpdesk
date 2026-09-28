<template>
  <Filter
    :filterable-fields="fields"
    :conditions="conditions"
    @update:conditions="(next: FilterCondition[]) => emit('update:conditions', next)"
  />
</template>

<script setup lang="ts">
// Prop-driven: a Studio page script has no component to `provide` from.
import { Filter } from "@helpdesk/shared/filter";
import type { FilterCondition, FilterField } from "@helpdesk/shared/filter";

defineProps<{ fields?: FilterField[]; conditions?: FilterCondition[] }>();
const emit = defineEmits<{
  "update:conditions": [conditions: FilterCondition[]];
}>();
</script>
