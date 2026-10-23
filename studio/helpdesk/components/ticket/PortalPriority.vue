<template>
  <div class="min-w-0 flex-1 text-base text-ink-gray-8">
    <PriorityCell />
  </div>
</template>

<script setup lang="ts">
import { priorityCell } from "@app/components/list/ticketCells";

const props = defineProps<{ priority: string }>();

const PriorityCell = () => priorityCell({ item: props.priority });
</script>
