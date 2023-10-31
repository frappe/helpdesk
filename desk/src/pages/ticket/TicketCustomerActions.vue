<template>
  <span class="flex gap-2">
    <Button
      v-if="showReopenButton"
      label="Reopen"
      theme="gray"
      variant="solid"
      @click="() => ticket.setValue.submit({ status: 'Open' })"
    >
      <template #prefix>
        <LucideRepeat class="h-4 w-4" />
      </template>
    </Button>
    <Button
      v-if="showResolveButton"
      label="Resolve"
      theme="gray"
      variant="solid"
    >
      <template #prefix>
        <LucideCheck class="h-4 w-4" />
      </template>
    </Button>
  </span>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { Ticket } from "./symbols";

const ticket = inject(Ticket);
const showReopenButton = computed(
  () => ticket.doc.status === "Resolved" && !ticket.doc.feedback
);
const showResolveButton = computed(() =>
  ["Open", "Replied"].includes(ticket.doc.status)
);
</script>
