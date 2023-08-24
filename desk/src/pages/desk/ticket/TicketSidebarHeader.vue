<template>
  <div class="flex items-center justify-between border-b px-5 py-3">
    <div class="text-lg font-semibold text-gray-900">
      {{ title }}
    </div>
    <Button
      theme="gray"
      variant="ghost"
      @click="ticketStore.sidebar.isExpanded = false"
    >
      <template #icon>
        <Icon icon="lucide:x" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Icon } from "@iconify/vue";
import { useTicketStore } from "./data";

interface P {
  title: string;
}

defineProps<P>();
const ticketStore = useTicketStore();
</script>
