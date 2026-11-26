<template>
  <span
    v-if="priority"
    class="flex min-w-0 items-center gap-2"
    :class="{ 'me-1': iconOnly }"
  >
    <span class="flex h-3.5 w-3.5 shrink-0 items-center justify-center">
      <PriorityIcon :level="level" />
    </span>
    <span v-if="!iconOnly" :title="priority" class="truncate">{{
      priority
    }}</span>
  </span>
</template>

<script setup lang="ts">
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { PriorityIcon } from "@helpdesk/shared/ticketCells";
import { computed } from "vue";

const props = defineProps<{
  priority?: string;
  iconOnly?: boolean;
}>();

const { getLevel } = useTicketPriorityStore();

const level = computed(() => getLevel(props.priority ?? ""));
</script>
