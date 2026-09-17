<template>
  <Filter
    :filterable-fields="fields"
    :conditions="conditions"
    @update:conditions="(next: FilterCondition[]) => emit('update:conditions', next)"
  />
</template>

<script setup lang="ts">
// The desk's filter popover, driven by props: a Studio page script returns bindings and
// has no component of its own to `provide` from. Named `KbFilter` because Studio
// registers a custom component by its filename.
import { Filter } from '@helpdesk/shared/filter'
import type { FilterCondition, FilterField } from '@helpdesk/shared/filter'

defineProps<{ fields?: FilterField[]; conditions?: FilterCondition[] }>()
const emit = defineEmits<{ 'update:conditions': [conditions: FilterCondition[]] }>()
</script>
