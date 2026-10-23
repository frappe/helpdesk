<template>
  <!-- 16px slot: text lines up with the other icon rows. -->
  <div class="flex min-w-0 flex-1 items-center gap-2 text-base text-ink-gray-8">
    <span class="flex size-4 shrink-0 items-center justify-center">
      <PriorityIcon :level="getPriorityLevel(priority)" />
    </span>
    <span class="truncate">{{ priority }}</span>
  </div>
</template>

<script setup lang="ts">
import { PriorityIcon } from "@helpdesk/shared/ticketCells";
import { getPriorityLevel } from "@app/stores/ticketMeta";

defineProps<{ priority: string }>();
</script>
